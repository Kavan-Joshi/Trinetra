"""Live viewing service (Workstream 2).

Serves per-camera live video to the operator console via two transports:

* **HLS** (default, ~3-10 s latency) — generated on demand by an ffmpeg process
  per camera. In simulation mode ffmpeg reads a ``testsrc`` pattern with the
  camera name + clock overlaid; in live mode it reads the camera's RTSP URL.
  Only one ffmpeg process per camera runs, and only while an operator is
  watching (idle processes are reaped) — consistent with "move events, not
  video": a stream is pulled only on operator demand.

* **WebRTC** (opt-in, sub-second) — a WHIP endpoint (``POST /whip/{cam}``)
  backed by aiortc that publishes a generated video track. Enable at build time
  with ``INSTALL_WEBRTC=true``; if aiortc is absent the endpoint returns 503 and
  the console falls back to HLS.
"""

import asyncio
import base64
import logging
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, PlainTextResponse

from trinetra_core.config import settings
from trinetra_core.db import CameraRow, SessionLocal

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trinetra.streamer")

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
HLS_ROOT = Path(os.getenv("TRINETRA_STREAMER_DIR", "/tmp/hls"))
HLS_ROOT.mkdir(parents=True, exist_ok=True)
IDLE_TIMEOUT = 60.0
PLAYLIST_READY_TIMEOUT = 24.0
MAX_CONCURRENT_STREAMS = 9


async def _get_camera(cam_id: str) -> dict | None:
    """Look up a camera in the registry DB (works for sim + real grid cameras)."""
    async with SessionLocal() as session:
        row = await session.get(CameraRow, cam_id)
    if not row:
        return None
    return {"id": row.id, "name": row.name, "stream_url": row.stream_url}


class StreamManager:
    def __init__(self):
        self._streams: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    def _source_args(self, cam: dict, force_sim: bool = False) -> list[str]:
        mode = os.getenv("TRINETRA_STREAMER_MODE", "sim").lower()
        if not force_sim and mode == "live" and cam.get("stream_url", "").startswith("rtsp://"):
            return ["-rtsp_transport", "tcp", "-i", cam["stream_url"]]
        name = cam.get("name", cam.get("id", "")).replace(":", " ").replace("'", "")
        cid = cam.get("id", "")
        return [
            "-re", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=10",
            "-vf",
            (f"drawtext=fontfile={FONT}:text='{name} ({cid})':"
             "x=10:y=10:fontsize=22:fontcolor=white,"
             f"drawtext=fontfile={FONT}:text='%{{localtime}}':x=10:y=332:fontsize=14:fontcolor=white"),
        ]

    def _spawn(self, cam: dict, cam_dir: Path, playlist: Path, mode: str = "copy"):
        """mode: copy (remux H.264) | transcode (re-encode to H.264, for H.265) | sim (testsrc)."""
        force_sim = mode == "sim"
        source = self._source_args(cam, force_sim=force_sim)
        if mode == "copy":
            enc = ["-c:v", "copy", "-an"]
            label = "live RTSP (copy/remux)"
        elif mode == "transcode":
            # HEVC/H.265 → H.264 at 720p (hls.js can't play HEVC/TS; re-encode for browser compat)
            enc = ["-c:v", "libx264", "-preset", "veryfast", "-vf", "scale=1280:720",
                   "-pix_fmt", "yuv420p", "-g", "20", "-b:v", "2500k", "-an"]
            label = "live RTSP (transcode→H.264 720p)"
        else:
            enc = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "20", "-an"]
            label = "sim (testsrc)"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", *source, *enc,
               "-f", "hls", "-hls_time", "2", "-hls_list_size", "6",
               "-hls_flags", "delete_segments+append_list", str(playlist)]
        log.info("starting ffmpeg for %s [%s]: %s ...", cam.get("id"), label, " ".join(cmd[:6]))
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def _probe_codec(self, url: str) -> str:
        """Probe the RTSP video codec so we copy H.264 (full quality) but transcode
        HEVC (hls.js cannot play HEVC in MPEG-TS segments)."""
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-rtsp_transport", "tcp", "-select_streams", "v:0",
                 "-show_entries", "stream=codec_name", "-of", "default=nw=1:nk=1", url],
                capture_output=True, text=True, timeout=15,
            )
            return (out.stdout.strip().splitlines()[0].lower() if out.stdout.strip() else "")
        except Exception:
            return ""

    async def ensure(self, cam_id: str) -> Path:
        async with self._lock:
            entry = self._streams.get(cam_id)
            if entry:
                entry["last_access"] = time.monotonic()
                return entry["dir"]
            if len(self._streams) >= MAX_CONCURRENT_STREAMS:
                raise HTTPException(503, "max concurrent streams reached — try again shortly")
            cam = await _get_camera(cam_id)
            if not cam:
                raise HTTPException(404, f"unknown camera {cam_id}")
            cam_dir = HLS_ROOT / cam_id
            cam_dir.mkdir(parents=True, exist_ok=True)
            for f in cam_dir.glob("*"):
                f.unlink()
            playlist = cam_dir / "playlist.m3u8"
            entry = {"proc": None, "dir": cam_dir, "playlist": playlist, "last_access": time.monotonic(), "cam": cam}
            self._streams[cam_id] = entry

        # choose attempt chain based on the source codec:
        #  H.264  → copy (full quality, hls.js-playable)
        #  HEVC   → transcode to H.264 (hls.js can't play HEVC/TS)
        #  sim cameras (no real RTSP) skip straight to sim.
        mode = os.getenv("TRINETRA_STREAMER_MODE", "sim").lower()
        is_rtsp = mode == "live" and cam.get("stream_url", "").startswith("rtsp://")
        if is_rtsp:
            codec = await asyncio.to_thread(self._probe_codec, cam["stream_url"])
            if codec == "h264":
                attempts = ["copy", "transcode", "sim"]
            elif codec:
                log.info("%s source codec=%s → transcode to H.264", cam_id, codec)
                attempts = ["transcode", "sim"]
            else:
                attempts = ["copy", "transcode", "sim"]
        else:
            attempts = ["sim"]

        for attempt, sp_mode in enumerate(attempts):
            playlist.unlink(missing_ok=True)
            async with self._lock:
                entry["proc"] = self._spawn(cam, cam_dir, playlist, mode=sp_mode)
            if attempt > 0:
                log.info("retrying %s with %s", cam_id, sp_mode)
            deadline = time.monotonic() + PLAYLIST_READY_TIMEOUT
            died = False
            while time.monotonic() < deadline:
                # a real segment must exist (not just the playlist header) before we serve
                if any(f.stat().st_size > 1024 for f in cam_dir.glob("*.ts")):
                    return cam_dir
                if entry["proc"].poll() is not None:
                    err = entry["proc"].stderr.read().decode(errors="replace")[:200] if entry["proc"].stderr else ""
                    log.warning("ffmpeg [%s] exited early for %s: %s", sp_mode, cam_id, err.strip())
                    died = True
                    break
                await asyncio.sleep(0.4)
            if not died:
                # timed out waiting for playlist — kill and try next
                try:
                    entry["proc"].terminate()
                except Exception:
                    pass
        raise HTTPException(503, "stream not ready (camera offline or unreachable)")

    def touch(self, cam_id: str) -> None:
        entry = self._streams.get(cam_id)
        if entry:
            entry["last_access"] = time.monotonic()

    async def reap_loop(self) -> None:
        while True:
            await asyncio.sleep(10)
            now = time.monotonic()
            for cam_id, entry in list(self._streams.items()):
                if now - entry["last_access"] > IDLE_TIMEOUT:
                    log.info("reaping idle stream for %s", cam_id)
                    try:
                        entry["proc"].terminate()
                        entry["proc"].wait(timeout=3)
                    except Exception:
                        try:
                            entry["proc"].kill()
                        except Exception:
                            pass
                    self._streams.pop(cam_id, None)
                    shutil.rmtree(entry["dir"], ignore_errors=True)


manager = StreamManager()
app = FastAPI(title="Trinetra Streamer", version="1.0.0")


@app.on_event("startup")
async def _startup() -> None:
    asyncio.create_task(manager.reap_loop())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "streamer", "active_streams": len(manager._streams)}


@app.get("/hls/{cam_id}/playlist.m3u8")
async def hls_playlist(cam_id: str):
    await manager.ensure(cam_id)
    p = manager._streams[cam_id]["playlist"]
    manager.touch(cam_id)
    if not p.exists():
        raise HTTPException(503, "playlist not ready")
    return FileResponse(p, media_type="application/vnd.apple.mpegurl",
                        headers={"Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*"})


@app.get("/hls/{cam_id}/{segment}")
async def hls_segment(cam_id: str, segment: str):
    manager.touch(cam_id)
    seg = manager._streams.get(cam_id, {}).get("dir", HLS_ROOT / cam_id) / segment
    if not seg.exists():
        raise HTTPException(404, "segment not found")
    return FileResponse(seg, media_type="video/MP2T",
                        headers={"Access-Control-Allow-Origin": "*"})


# ---- WebRTC (WHEP signaling proxy to the grid) --------------------------- #

@app.post("/whip/{cam_id}")
async def whip(cam_id: str, request: Request):
    """Relay the browser's WebRTC offer to the grid's WHEP endpoint and return
    the grid's SDP answer. The grid serves real sub-second footage; we proxy the
    signaling server-side because browsers can't embed the email:password auth.
    Media (SRTP) then flows directly between the browser and the grid.
    """
    if not settings.grid_email or not settings.grid_password:
        raise HTTPException(503, "WebRTC requires grid credentials (TRINETRA_GRID_EMAIL/PASSWORD)")
    offer = await request.body()
    whep_url = f"http://{settings.grid_whep_host}/stream/{cam_id}/whep"
    token = base64.b64encode(f"{settings.grid_email}:{settings.grid_password}".encode()).decode()

    def _relay() -> bytes:
        req = urllib.request.Request(
            whep_url, data=offer, method="POST",
            headers={"Content-Type": "application/sdp", "Accept": "application/sdp",
                     "Authorization": f"Basic {token}"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read()

    try:
        answer = await asyncio.to_thread(_relay)
    except urllib.error.HTTPError as e:
        raise HTTPException(e.code, f"grid WHEP error: {e.reason}")
    except Exception as e:
        raise HTTPException(502, f"grid WHEP unreachable: {e}")
    return PlainTextResponse(answer, media_type="application/sdp",
                             headers={"Access-Control-Allow-Origin": "*"})
