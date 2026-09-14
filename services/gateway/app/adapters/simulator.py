import asyncio
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from trinetra_core.config import settings
from trinetra_core.models import DetectionEvent
from sim.snapshots import render_snapshot
from .base import BaseAdapter

log = logging.getLogger("trinetra.adapter.sim")


class SimulatedAdapter(BaseAdapter):
    def __init__(self, name: str, cameras, js, passes):
        super().__init__(name, cameras, js)
        self.passes = sorted([p for p in passes if p.camera_id in {c.id for c in cameras}], key=lambda p: p.offset_s)
        self.sim_dir = Path(settings.evidence_dir) / "sim"
        self.sim_dir.mkdir(parents=True, exist_ok=True)

    async def run(self) -> None:
        log.info("adapter[%s] simulating %d cameras, %d scripted passes", self.name, len(self.cameras), len(self.passes))
        t0 = time.monotonic()
        index = 0
        while index < len(self.passes):
            sim_elapsed = (time.monotonic() - t0) * settings.sim_speed
            while index < len(self.passes) and self.passes[index].offset_s <= sim_elapsed:
                spec = self.passes[index]
                index += 1
                try:
                    ts = datetime.now(timezone.utc)
                    fname = f"{spec.plate or spec.kind}_{spec.camera_id}_{int(spec.offset_s * 1000)}.png"
                    fpath = self.sim_dir / fname
                    render_snapshot(fpath, spec=spec, ts=ts)
                    await self.emit(DetectionEvent(
                        camera_id=spec.camera_id,
                        ts=ts,
                        kind=spec.kind,
                        plate_raw=spec.plate,
                        plate_confidence=spec.plate_confidence,
                        vehicle_class=spec.vehicle_class,
                        color=spec.color,
                        direction=spec.direction,
                        speed_kmh=spec.speed_kmh,
                        bbox=[180, 140, 460, 300] if spec.kind == "vehicle" else [260, 150, 380, 300],
                        attributes=spec.attributes,
                        snapshot_path=f"sim/{fname}",
                    ))
                except Exception:
                    log.exception("adapter[%s] failed to emit scripted pass %s@%s", self.name, spec.camera_id, spec.offset_s)
            await asyncio.sleep(0.25)
        log.info("adapter[%s] scenario playback complete (%d events) — gateway idle", self.name, self._emitted)
