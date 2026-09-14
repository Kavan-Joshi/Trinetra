import asyncio
import logging
import os
import re

from sqlalchemy import select

from trinetra_core.bus import connect
from trinetra_core.db import CameraRow, SessionLocal, init_db
from trinetra_core.models import Camera
from .adapters.simulator import SimulatedAdapter
# importing the live adapter modules registers them with the adapter registry
from .adapters import rtsp as _rtsp_adapters  # noqa: F401  (registers rtsp, onvif)
from .adapters import gb28181 as _gb28181_adapter  # noqa: F401  (registers gb28181)
from .adapters.registry import registry

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trinetra.gateway")


async def _cameras_from_registry(groups: list[str]) -> list[Camera]:
    """Load online cameras from the registry DB (live mode).

    Optional ``TRINETRA_GATEWAY_CAMERA_FILTER`` (regex) restricts which camera
    ids are processed — e.g. ``^cam\\d+$`` to run analytics only on the real
    grid cameras and skip synthetic/sim cameras with unreachable URLs.
    """
    await init_db()
    flt = os.getenv("TRINETRA_GATEWAY_CAMERA_FILTER", "").strip()
    pattern = re.compile(flt) if flt else None
    async with SessionLocal() as session:
        rows = (await session.execute(select(CameraRow).where(CameraRow.status == "online"))).scalars().all()
    out = []
    for r in rows:
        if r.protocol not in groups:
            continue
        if pattern and not pattern.search(r.id):
            continue
        out.append(Camera(id=r.id, name=r.name, lat=r.lat, lon=r.lon, vendor=r.vendor, vms=r.vms,
                          protocol=r.protocol, status=r.status, department=r.department, zone=r.zone,
                          stream_url=r.stream_url, direction=r.direction))
    if pattern:
        log.info("camera filter '%s' -> %d camera(s)", flt, len(out))
    return out


async def main() -> None:
    mode = os.getenv("TRINETRA_GATEWAY_MODE", "simulation").lower()
    groups = [g.strip() for g in os.getenv("TRINETRA_GATEWAY_GROUPS", "rtsp,onvif,http-mjpeg,vendor-api,gb28181").split(",") if g.strip()]
    nc, js = await connect()
    adapters = []

    if mode == "simulation":
        from sim.data import CAMERAS
        from sim.scenario import build_scenario
        cameras = [Camera(**c) for c in CAMERAS if c["protocol"] in groups and c["status"] == "online"]
        for proto in groups:
            cams = [c for c in cameras if c.protocol == proto]
            if cams:
                adapters.append(SimulatedAdapter(proto, cams, js, build_scenario()))
    else:
        # live mode: cameras come from the registry DB (ingested from the grid catalogue)
        cameras = await _cameras_from_registry(groups)
        log.info("live mode: %d online camera(s) from registry", len(cameras))
        for proto in groups:
            cams = [c for c in cameras if c.protocol == proto]
            if not cams:
                continue
            adapter = registry.create(proto, cams, js)
            if adapter is None:
                log.warning("protocol group '%s' has no registered adapter (vendor-SDK federation — roadmap); skipped", proto)
                continue
            adapters.append(adapter)

    if not adapters:
        log.error("no adapters configured; mode=%s groups=%s", mode, groups)
        return
    log.info("gateway starting: mode=%s adapters=%s", mode, [a.name for a in adapters])
    await asyncio.gather(*(a.run() for a in adapters))
    if mode == "simulation":
        log.info("scenario playback complete — gateway idle (restart container or scripts/replay.ps1 to replay)")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
