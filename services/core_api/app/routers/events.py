from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.db import CameraRow, EventRow, TrackRow, get_session
from trinetra_core.models import RouteResponse, TrackPoint, TrackSession
from trinetra_core.plates import format_plate, normalize_plate
from ..auth import apply_scope, current_user

router = APIRouter(prefix="/api/v1", tags=["events"])


def evt_dict(r: EventRow) -> dict:
    return {
        "event_id": str(r.event_id), "camera_id": r.camera_id, "ts": r.ts.isoformat(),
        "kind": r.kind, "plate": r.plate_raw, "plate_norm": r.plate_norm,
        "plate_confidence": r.plate_confidence, "vehicle_class": r.vehicle_class,
        "color": r.color, "direction": r.direction, "speed_kmh": r.speed_kmh,
        "attributes": r.attributes, "snapshot_path": r.snapshot_path,
    }


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@router.get("/events")
async def search_events(
    camera_id: str | None = None,
    plate: str | None = None,
    kind: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    stmt = select(EventRow)
    if camera_id:
        stmt = stmt.where(EventRow.camera_id == camera_id)
    if plate:
        stmt = stmt.where(EventRow.plate_norm.ilike(f"%{normalize_plate(plate)}%"))
    if kind:
        stmt = stmt.where(EventRow.kind == kind)
    ts_from = parse_dt(date_from)
    ts_to = parse_dt(date_to)
    if ts_from:
        stmt = stmt.where(EventRow.ts >= ts_from)
    if ts_to:
        stmt = stmt.where(EventRow.ts <= ts_to)
    stmt = apply_scope(stmt, user, EventRow.camera_id)
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
    rows = (await session.execute(stmt.order_by(EventRow.ts.desc()).offset(offset).limit(min(limit, 500)))).scalars().all()
    return {"total": total, "items": [evt_dict(r) for r in rows]}


@router.get("/events/{event_id}")
async def get_event(event_id: str, session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    from uuid import UUID
    row = (await session.execute(select(EventRow).where(EventRow.event_id == UUID(event_id)))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "event not found")
    return evt_dict(row)


@router.get("/tracking/{plate}/route", response_model=RouteResponse)
async def vehicle_route(
    plate: str,
    date_from: str | None = None,
    date_to: str | None = None,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    norm = normalize_plate(plate)
    stmt = (
        select(TrackRow, CameraRow)
        .join(CameraRow, TrackRow.camera_id == CameraRow.id)
        .where(TrackRow.plate_norm == norm)
        .order_by(TrackRow.ts)
    )
    ts_from = parse_dt(date_from)
    ts_to = parse_dt(date_to)
    if ts_from:
        stmt = stmt.where(TrackRow.ts >= ts_from)
    if ts_to:
        stmt = stmt.where(TrackRow.ts <= ts_to)
    rows = (await session.execute(stmt)).all()
    sessions: dict[str, TrackSession] = {}
    for track, cam in rows:
        pt = TrackPoint(
            camera_id=cam.id, camera_name=cam.name, ts=track.ts, lat=track.lat, lon=track.lon,
            snapshot_path=None,
        )
        sessions.setdefault(track.session_id, TrackSession(session_id=track.session_id, points=[])).points.append(pt)
    return RouteResponse(
        plate=norm,
        display_plate=format_plate(norm),
        sessions=sorted(sessions.values(), key=lambda s: s.points[0].ts if s.points else datetime.min.replace(tzinfo=timezone.utc), reverse=True),
    )


@router.get("/tracking/recent")
async def recent_tracks(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    stmt = (
        select(TrackRow)
        .distinct(TrackRow.plate_norm)
        .order_by(TrackRow.plate_norm, TrackRow.ts.desc())
        .limit(min(limit, 100))
    )
    rows = (await session.execute(stmt)).scalars().all()
    out = []
    for r in rows:
        out.append({
            "plate": format_plate(r.plate_norm), "plate_norm": r.plate_norm,
            "last_camera": r.camera_id, "last_seen": r.ts.isoformat(),
            "lat": r.lat, "lon": r.lon,
        })
    out.sort(key=lambda x: x["last_seen"], reverse=True)
    return {"items": out}
