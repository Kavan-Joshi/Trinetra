"""Ingest the external live camera grid catalogue into the Trinetra registry.

Fetches ``cameras.json`` from the grid portal (HTTP basic auth with the
registered email + access password), then for each camera constructs the three
access URLs per the grid's published scheme:

    RTSP:  rtsp://<email%40>:<password>@<rtsp_host>/stream/<id>
    HLS:   <hls_base>/<id>/index.m3u8
    WHEP:  http://<email%40>:<password>@<whep_host>/stream/<id>/whep

and upserts them into the camera registry (protocol=rtsp, the RTSP URL is what
the gateway/streamer pull). Credentials come from environment only — never
committed. Run with:

    TRINETRA_GRID_EMAIL=you@example.com TRINETRA_GRID_PASSWORD=... \
        python -m scripts.ingest_catalogue      # or: docker compose run --rm ingester
"""

import asyncio
import base64
import datetime as _dt
import json
import logging
import math
import urllib.request

from sqlalchemy import select

from trinetra_core.config import settings
from trinetra_core.db import CameraRow, DepartmentRow, SessionLocal, init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trinetra.ingester")

# The 5 hackathon dataset departments (Health, Police, GSRTC, Panchayat, Municipal).
# Grid cameras are assigned round-robin to these.
GRID_DEPARTMENTS = [
    ("health", "Health & Family Welfare (Hospitals)"),
    ("police_scr", "Gujarat Police — State Control Room"),
    ("gsrtc", "GSRTC (Gujarat State Road Transport)"),
    ("panchayat", "Panchayat (Rural Development)"),
    ("ud", "Urban Development (Municipal)"),
]


def _encoded_email() -> str:
    return (settings.grid_email or "").replace("@", "%40")


def _rtsp_url(cam_id: str) -> str:
    return f"rtsp://{_encoded_email()}:{settings.grid_password}@{settings.grid_rtsp_host}/stream/{cam_id}"


def _hls_url(cam_id: str) -> str:
    return f"{settings.grid_hls_base}/{cam_id}/index.m3u8"


def _whep_url(cam_id: str) -> str:
    return f"http://{_encoded_email()}:{settings.grid_password}@{settings.grid_whep_host}/stream/{cam_id}/whep"


def fetch_catalogue() -> list:
    if not settings.grid_email or not settings.grid_password:
        raise RuntimeError("TRINETRA_GRID_EMAIL / TRINETRA_GRID_PASSWORD not set — cannot authenticate to the grid")
    url = settings.grid_catalogue_url
    log.info("fetching catalogue %s", url)
    token = base64.b64encode(f"{settings.grid_email}:{settings.grid_password}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        ctype = resp.headers.get("Content-Type", "")
        body = resp.read().decode("utf-8", errors="replace")
    if "json" not in ctype and not body.lstrip().startswith(("[", "{")):
        raise RuntimeError(f"catalogue returned non-JSON (likely the login page). Content-Type: {ctype}")
    return json.loads(body)


def _iter_cameras(data) -> list[dict]:
    """Normalise the catalogue payload to a list of {id, name, lat, lon} dicts."""
    if isinstance(data, dict):
        items = data.get("cameras") or data.get("items") or data.get("data") or []
    else:
        items = data
    out: list[dict] = []
    for i, item in enumerate(items):
        if isinstance(item, str):
            out.append({"id": item, "name": item, "lat": None, "lon": None})
        elif isinstance(item, dict):
            cid = item.get("id") or item.get("camera_id") or item.get("name") or item.get("slug")
            if not cid:
                continue
            name = item.get("name") or item.get("label") or cid
            lat = item.get("lat") or item.get("latitude")
            lon = item.get("lon") or item.get("longitude") or item.get("lng")
            out.append({"id": str(cid), "name": str(name), "lat": lat, "lon": lon})
    return out


def _spread_coord(i: int, n: int, base: float, deg: float) -> float:
    """Deterministic jitter so un-located cameras don't stack on one point."""
    if n <= 1:
        return base
    angle = 2 * math.pi * i / n
    radius = 0.01
    return round(base + radius * math.cos(angle) + 0.002 * i, 6)


async def ingest() -> None:
    await init_db()
    try:
        cameras = _iter_cameras(fetch_catalogue())
        log.info("catalogue contains %d camera(s)", len(cameras))
    except Exception as e:
        log.warning("catalogue fetch failed (%s) — falling back to cam01..cam30 from the published ID range", e)
        cameras = [{"id": f"cam{i:02d}", "name": f"Grid Camera {i:02d}", "lat": None, "lon": None}
                   for i in range(1, 31)]
    if not cameras:
        return
    today = _dt.date.today()
    n = len(cameras)
    created = updated = 0
    # resolve department ids for the 5 hackathon departments
    dept_ids: dict[str, int] = {}
    async with SessionLocal() as s:
        for code, _name in GRID_DEPARTMENTS:
            row = (await s.execute(select(DepartmentRow).where(DepartmentRow.code == code))).scalar_one_or_none()
            if row:
                dept_ids[code] = row.id
    async with SessionLocal() as s:
        for i, c in enumerate(cameras):
            cid = c["id"]
            lat = float(c["lat"]) if c["lat"] is not None else _spread_coord(i, n, settings.grid_default_lat, 0)
            lon = float(c["lon"]) if c["lon"] is not None else _spread_coord(i, n, settings.grid_default_lon, 0)
            dept_code, dept_name = GRID_DEPARTMENTS[i % len(GRID_DEPARTMENTS)]
            row = await s.get(CameraRow, cid)
            fields = dict(
                name=c["name"], lat=lat, lon=lon, vendor="Grid", vms="Sentinel Grid",
                protocol="rtsp", status="online", department=dept_name,
                department_id=dept_ids.get(dept_code),
                zone="External Grid", stream_url=_rtsp_url(cid), direction="",
                source_type="gov", consent=False, install_date=today,
                health="healthy", maintenance_status="ok", coverage_radius_m=80, firmware="grid",
            )
            if row:
                for k, v in fields.items():
                    setattr(row, k, v)
                updated += 1
            else:
                s.add(CameraRow(id=cid, **fields))
                created += 1
            log.info("  %s — %s | rtsp=%s | hls=%s", cid, c["name"], _rtsp_url(cid), _hls_url(cid))
        await s.commit()
    log.info("ingest complete: %d created, %d updated", created, updated)


if __name__ == "__main__":
    asyncio.run(ingest())
