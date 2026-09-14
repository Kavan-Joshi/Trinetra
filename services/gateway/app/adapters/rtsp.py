import asyncio
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

from trinetra_core.config import settings
from trinetra_core.models import DetectionEvent
from .base import BaseAdapter
from .registry import registry

log = logging.getLogger("trinetra.adapter.rtsp")

# RTSP is pulled by an ffmpeg subprocess (not cv2.VideoCapture) so that ffmpeg
# handles the grid's auth challenge (OpenCV's ffmpeg backend does not retry 401s
# with credentials). TCP is forced (UDP corrupts frames across NAT/firewalls).
POLL_INTERVAL = 0.5
DETECT_EVERY = 5.0
RECONNECT_MIN = 2.0
RECONNECT_MAX = 30.0
# frame size the pipeline analyses (downscaled from 1080p for CPU feasibility,
# but high enough for ANPR to read plates)
FRAME_W, FRAME_H = 1280, 720
FRAME_BYTES = FRAME_W * FRAME_H * 3


class RTSPAdapter(BaseAdapter):
    def __init__(self, name: str, cameras, js):
        super().__init__(name, cameras, js)
        self.pipeline = None
        self.plate_history: dict[str, float] = {}
        self.face_history: dict[str, float] = {}

    async def run(self) -> None:
        try:
            from ..pipeline import get_analytics_engine
        except Exception as e:
            log.error("adapter[%s] ML extras not installed (%s); build with INSTALL_ML=true for live inference", self.name, e)
            return
        self.pipeline = get_analytics_engine(Path(settings.evidence_dir) / "live")
        for cam in self.cameras:
            if not cam.stream_url:
                log.warning("adapter[%s] camera %s has no stream_url; skipping", self.name, cam.id)
                continue
            asyncio.create_task(self._stream_camera(cam))
        await asyncio.Future()

    def _ffmpeg_cmd(self, url: str) -> list[str]:
        return [
            "ffmpeg", "-y", "-loglevel", "error",
            "-rtsp_transport", "tcp", "-i", url,
            "-an", "-vf", f"scale={FRAME_W}:{FRAME_H}",
            "-r", "2",  # 2fps output — drastically reduces decode + pipe CPU
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-",
        ]

    async def _stream_camera(self, cam) -> None:
        import numpy as np

        host = cam.stream_url.split("@")[-1]
        log.info("adapter[%s] opening %s -> %s", self.name, cam.id, host)
        backoff = RECONNECT_MIN
        last_detect = 0.0

        while True:
            cmd = self._ffmpeg_cmd(cam.stream_url)
            try:
                proc = await asyncio.to_thread(
                    subprocess.Popen, cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
                )
            except Exception as e:
                log.warning("adapter[%s] ffmpeg spawn failed for %s: %s", self.name, cam.id, e)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, RECONNECT_MAX)
                continue

            # read frames from the raw BGR pipe
            while True:
                buf = await asyncio.to_thread(proc.stdout.read, FRAME_BYTES)
                if len(buf) < FRAME_BYTES:
                    # EOF / stream ended — reconnect with backoff
                    break
                backoff = RECONNECT_MIN
                frame = np.frombuffer(buf, dtype=np.uint8).reshape((FRAME_H, FRAME_W, 3))

                now = time.monotonic()
                if now - last_detect < DETECT_EVERY:
                    continue
                last_detect = now

                try:
                    detections = await asyncio.to_thread(self.pipeline.process, frame, cam)
                except Exception:
                    log.exception("adapter[%s] inference error on %s", self.name, cam.id)
                    continue

                for d in detections:
                    kind = d.get("kind", "vehicle")
                    ts = datetime.now(timezone.utc)
                    live_dir = Path(settings.evidence_dir) / "live"
                    live_dir.mkdir(parents=True, exist_ok=True)

                    if kind == "vehicle":
                        plate = d.get("plate")
                        if not plate:
                            continue
                        key = f"{cam.id}:{plate}"
                        if now - self.plate_history.get(key, 0) < 120:
                            continue
                        # fuzzy dedup: skip if too similar to a recent plate on the
                        # same camera (OCR variance — e.g. S/R confusion, shifted digits)
                        skip = False
                        for prev_key, prev_time in list(self.plate_history.items()):
                            if not prev_key.startswith(f"{cam.id}:"):
                                continue
                            if now - prev_time > 30:
                                continue
                            prev_plate = prev_key.split(":", 1)[1]
                            if prev_plate == plate:
                                continue
                            ratio = SequenceMatcher(None, plate, prev_plate).ratio()
                            if ratio >= 0.8:
                                skip = True
                                log.info("adapter[%s] fuzzy dedup: %s ~ %s (ratio %.2f) — skipping", self.name, plate, prev_plate, ratio)
                                break
                        if skip:
                            continue
                        self.plate_history[key] = now
                        fname = f"{cam.id}_{plate}_{int(ts.timestamp())}.png"
                        await asyncio.to_thread(d["save_snapshot"], str(live_dir / fname))
                        await self.emit(DetectionEvent(
                            camera_id=cam.id, ts=ts, kind="vehicle",
                            plate_raw=plate, plate_confidence=d.get("plate_confidence"),
                            vehicle_class=d.get("vehicle_class"), color=d.get("color"),
                            direction=cam.direction or None, speed_kmh=None, bbox=d.get("bbox"),
                            attributes={"source": "live", "adapter": self.name, "engine": type(self.pipeline).__name__},
                            snapshot_path=f"live/{fname}",
                        ))
                    elif kind == "person" and d.get("face"):
                        # one face event per camera per 5 min (avoid flooding)
                        key = f"{cam.id}:face"
                        if now - self.face_history.get(key, 0) < 300:
                            continue
                        self.face_history[key] = now
                        fname = f"{cam.id}_face_{int(ts.timestamp())}.png"
                        await asyncio.to_thread(d["save_snapshot"], str(live_dir / fname))
                        await self.emit(DetectionEvent(
                            camera_id=cam.id, ts=ts, kind="person",
                            plate_raw=None, plate_confidence=d.get("plate_confidence"), vehicle_class=None,
                            color=None, direction=cam.direction or None, speed_kmh=None,
                            bbox=d.get("bbox"),
                            attributes={"source": "live", "adapter": self.name, "face": True,
                                        "embedding": d.get("embedding"),
                                        "engine": type(self.pipeline).__name__},
                            snapshot_path=f"live/{fname}",
                        ))
            # stream ended — clean up and reconnect
            try:
                proc.terminate()
            except Exception:
                pass
            log.warning("adapter[%s] stream %s ended — reconnecting in %.1fs", self.name, cam.id, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, RECONNECT_MAX)


# register for the RTSP and ONVIF protocol groups (ONVIF resolves to an RTSP
# media URI, so it reuses the RTSP adapter — see HLD §2)
registry.register("rtsp", RTSPAdapter)
registry.register("onvif", RTSPAdapter)
