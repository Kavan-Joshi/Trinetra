import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.db import CameraRow, get_session
from trinetra_core.models import Camera
from ..auth import apply_scope, audit, current_user, require_role

router = APIRouter(prefix="/api/v1/cameras", tags=["registry"])


def cam_dict(r: CameraRow) -> dict:
    return {
        "id": r.id, "name": r.name, "lat": r.lat, "lon": r.lon, "vendor": r.vendor,
        "vms": r.vms, "protocol": r.protocol, "status": r.status, "department": r.department,
        "department_id": r.department_id, "zone": r.zone, "stream_url": r.stream_url,
        "direction": r.direction, "source_type": r.source_type, "consent": r.consent,
        "install_date": r.install_date.isoformat() if r.install_date else None,
        "health": r.health, "maintenance_status": r.maintenance_status,
        "coverage_radius_m": r.coverage_radius_m, "firmware": r.firmware,
        "last_heartbeat": r.last_heartbeat.isoformat() if r.last_heartbeat else None,
    }


class CameraPatch(BaseModel):
    status: str | None = None
    name: str | None = None
    department: str | None = None
    stream_url: str | None = None
    health: str | None = None
    maintenance_status: str | None = None
    coverage_radius_m: int | None = None
    firmware: str | None = None
    install_date: str | None = None


@router.get("")
async def list_cameras(
    status: str | None = None,
    zone: str | None = None,
    department_id: int | None = None,
    health: str | None = None,
    maintenance_status: str | None = None,
    q: str | None = None,
    limit: int = 500,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    stmt = select(CameraRow)
    if status:
        stmt = stmt.where(CameraRow.status == status)
    if zone:
        stmt = stmt.where(CameraRow.zone == zone)
    if department_id:
        stmt = stmt.where(CameraRow.department_id == department_id)
    if health:
        stmt = stmt.where(CameraRow.health == health)
    if maintenance_status:
        stmt = stmt.where(CameraRow.maintenance_status == maintenance_status)
    if q:
        stmt = stmt.where(or_(CameraRow.name.ilike(f"%{q}%"), CameraRow.id.ilike(f"%{q}%")))
    stmt = apply_scope(stmt, user, CameraRow.id)
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
    rows = (await session.execute(stmt.order_by(CameraRow.id).offset(offset).limit(limit))).scalars().all()
    return {"total": total, "items": [cam_dict(r) for r in rows]}


@router.get("/health")
async def camera_health_summary(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    """Camera health & maintenance-status overview for monitoring dashboards."""
    rows = (await session.execute(select(CameraRow))).scalars().all()
    by_health: dict[str, int] = {}
    by_maintenance: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for c in rows:
        by_health[c.health] = by_health.get(c.health, 0) + 1
        by_maintenance[c.maintenance_status] = by_maintenance.get(c.maintenance_status, 0) + 1
        by_status[c.status] = by_status.get(c.status, 0) + 1
    return {
        "total": len(rows),
        "by_health": by_health,
        "by_maintenance": by_maintenance,
        "by_status": by_status,
        "needs_attention": sum(1 for c in rows if c.health != "healthy" or c.maintenance_status != "ok"),
    }


@router.get("/export")
async def export_cameras(
    zone: str | None = None,
    department_id: int | None = None,
    health: str | None = None,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    """Export the camera registry as CSV (Model-1 metadata export)."""
    stmt = select(CameraRow)
    if zone:
        stmt = stmt.where(CameraRow.zone == zone)
    if department_id:
        stmt = stmt.where(CameraRow.department_id == department_id)
    if health:
        stmt = stmt.where(CameraRow.health == health)
    stmt = apply_scope(stmt, user, CameraRow.id)
    rows = (await session.execute(stmt.order_by(CameraRow.id))).scalars().all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "name", "lat", "lon", "vendor", "vms", "protocol", "status", "department",
                "zone", "direction", "source_type", "install_date", "health", "maintenance_status",
                "coverage_radius_m", "firmware"])
    for r in rows:
        w.writerow([r.id, r.name, r.lat, r.lon, r.vendor, r.vms, r.protocol, r.status, r.department,
                    r.zone, r.direction, r.source_type,
                    r.install_date.isoformat() if r.install_date else "",
                    r.health, r.maintenance_status, r.coverage_radius_m, r.firmware])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trinetra-camera-registry.csv"},
    )


@router.get("/{camera_id}")
async def get_camera(camera_id: str, session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    row = await session.get(CameraRow, camera_id)
    if not row:
        raise HTTPException(404, "camera not found")
    return cam_dict(row)


@router.get("/{camera_id}/stream")
async def camera_stream_url(camera_id: str, session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    from trinetra_core.config import settings

    if not settings.streamer_enabled:
        raise HTTPException(503, "streaming service disabled")
    row = await session.get(CameraRow, camera_id)
    if not row:
        raise HTTPException(404, "camera not found")
    return {
        "camera_id": camera_id,
        "name": row.name,
        "source_type": row.source_type,
        "hls_url": f"/stream/hls/{camera_id}/playlist.m3u8",
        "webrtc_url": f"/stream/whip/{camera_id}",
        "ttl": settings.stream_token_ttl_seconds,
        "transport": "hls+webrtc",
    }


@router.post("")
async def create_camera(cam: Camera, session: AsyncSession = Depends(get_session), user=Depends(require_role("admin"))):
    if await session.get(CameraRow, cam.id):
        raise HTTPException(409, "camera id already exists")
    row = CameraRow(**cam.model_dump())
    session.add(row)
    await audit(session, user.username, "camera.create", cam.id, {"name": cam.name})
    await session.commit()
    return cam_dict(row)


@router.post("/bulk")
async def bulk_cameras(
    cams: list[Camera],
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin")),
):
    created = updated = 0
    for cam in cams:
        row = await session.get(CameraRow, cam.id)
        if row:
            for k, v in cam.model_dump().items():
                setattr(row, k, v)
            updated += 1
        else:
            session.add(CameraRow(**cam.model_dump()))
            created += 1
    await audit(session, user.username, "camera.bulk_upsert", "cameras", {"created": created, "updated": updated})
    await session.commit()
    return {"created": created, "updated": updated}


@router.post("/import")
async def import_cameras(request: Request, session: AsyncSession = Depends(get_session), user=Depends(require_role("admin"))):
    """Bulk CSV import of camera metadata (Model-1 onboarding).

    Expected columns: id,name,lat,lon,vendor,vms,protocol,department,zone,stream_url,
    direction,install_date,health,maintenance_status,coverage_radius_m,firmware
    """
    body = (await request.body()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(body))
    created = updated = skipped = 0
    for raw in reader:
        cam_id = (raw.get("id") or "").strip()
        if not cam_id:
            skipped += 1
            continue
        row = await session.get(CameraRow, cam_id)
        fields = {
            "name": (raw.get("name") or "").strip() or cam_id,
            "lat": float(raw.get("lat") or 0),
            "lon": float(raw.get("lon") or 0),
            "vendor": (raw.get("vendor") or "Unknown").strip(),
            "vms": (raw.get("vms") or "Standalone NVR").strip(),
            "protocol": (raw.get("protocol") or "rtsp").strip(),
            "department": (raw.get("department") or "Surveillance Cell").strip(),
            "zone": (raw.get("zone") or "Zone-1").strip(),
            "stream_url": (raw.get("stream_url") or "").strip(),
            "direction": (raw.get("direction") or "").strip(),
            "health": (raw.get("health") or "healthy").strip(),
            "maintenance_status": (raw.get("maintenance_status") or "ok").strip(),
            "coverage_radius_m": int(raw.get("coverage_radius_m") or 80),
            "firmware": (raw.get("firmware") or "").strip(),
        }
        from datetime import date as _date
        idate = (raw.get("install_date") or "").strip()
        if idate:
            try:
                fields["install_date"] = _date.fromisoformat(idate)
            except ValueError:
                pass
        if row:
            for k, v in fields.items():
                setattr(row, k, v)
            updated += 1
        else:
            session.add(CameraRow(id=cam_id, **fields))
            created += 1
    await audit(session, user.username, "camera.import", "cameras", {"created": created, "updated": updated, "skipped": skipped})
    await session.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


@router.patch("/{camera_id}")
async def patch_camera(
    camera_id: str,
    patch: CameraPatch,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin")),
):
    row = await session.get(CameraRow, camera_id)
    if not row:
        raise HTTPException(404, "camera not found")
    data = patch.model_dump(exclude_none=True)
    if "install_date" in data and data["install_date"]:
        from datetime import date as _date
        try:
            data["install_date"] = _date.fromisoformat(data["install_date"])
        except ValueError:
            del data["install_date"]
    for k, v in data.items():
        setattr(row, k, v)
    await audit(session, user.username, "camera.update", camera_id, patch.model_dump(exclude_none=True))
    await session.commit()
    return cam_dict(row)
