from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.db import AlertRow, AuditRow, CameraRow, EventRow, WatchlistRow, get_session
from ..auth import apply_scope, audit, current_user, require_role

router = APIRouter(prefix="/api/v1", tags=["alerts"])


def alert_dict(r: AlertRow) -> dict:
    return {
        "alert_id": str(r.alert_id), "event_id": str(r.event_id), "watchlist_id": r.watchlist_id,
        "category": r.category, "title": r.title, "plate": r.plate, "description": r.description,
        "camera_id": r.camera_id, "ts": r.ts.isoformat(), "confidence": r.confidence,
        "lat": r.lat, "lon": r.lon, "snapshot_path": r.snapshot_path,
        "status": r.status, "assigned_to": r.assigned_to,
        "source_system": r.source_system, "source_ref": r.source_ref, "enrichment": r.enrichment or {},
    }


@router.get("/alerts")
async def list_alerts(
    status: str | None = None,
    category: str | None = None,
    plate: str | None = None,
    camera_id: str | None = None,
    department_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    stmt = select(AlertRow)
    if status:
        stmt = stmt.where(AlertRow.status == status)
    if category:
        stmt = stmt.where(AlertRow.category == category)
    if plate:
        stmt = stmt.where(AlertRow.plate.ilike(f"%{plate}%"))
    if camera_id:
        stmt = stmt.where(AlertRow.camera_id == camera_id)
    if department_id:
        stmt = stmt.where(AlertRow.camera_id.in_(select(CameraRow.id).where(CameraRow.department_id == department_id)))
    stmt = apply_scope(stmt, user, AlertRow.camera_id)
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
    rows = (await session.execute(stmt.order_by(AlertRow.ts.desc()).offset(offset).limit(min(limit, 500)))).scalars().all()
    return {"total": total, "items": [alert_dict(r) for r in rows]}


@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str, session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    from uuid import UUID
    row = (await session.execute(select(AlertRow).where(AlertRow.alert_id == UUID(alert_id)))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "alert not found")
    return alert_dict(row)


class AlertPatch(BaseModel):
    status: str
    assigned_to: str | None = None


@router.patch("/alerts/{alert_id}")
async def patch_alert(
    alert_id: str,
    patch: AlertPatch,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin", "operator", "analyst")),
):
    from uuid import UUID
    if patch.status not in {"new", "ack", "resolved"}:
        raise HTTPException(422, "status must be new|ack|resolved")
    row = (await session.execute(select(AlertRow).where(AlertRow.alert_id == UUID(alert_id)))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "alert not found")
    row.status = patch.status
    row.assigned_to = patch.assigned_to or user.username
    await audit(session, user.username, "alert.update", alert_id, patch.model_dump())
    await session.commit()
    return alert_dict(row)


@router.get("/stats/overview")
async def stats_overview(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)

    async def count(stmt) -> int:
        return (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar()

    cam_total = apply_scope(select(CameraRow.id), user, CameraRow.id)
    cam_online = apply_scope(select(CameraRow.id).where(CameraRow.status == "online"), user, CameraRow.id)
    evt_stmt = apply_scope(select(EventRow.id).where(EventRow.ts >= day_ago), user, EventRow.camera_id)
    alerts_stmt = apply_scope(select(AlertRow.id).where(AlertRow.ts >= day_ago), user, AlertRow.camera_id)
    alerts_active_stmt = apply_scope(select(AlertRow.id).where(AlertRow.status.in_(["new", "ack"])), user, AlertRow.camera_id)

    return {
        "cameras_total": await count(cam_total),
        "cameras_online": await count(cam_online),
        "events_24h": await count(evt_stmt),
        "alerts_24h": await count(alerts_stmt),
        "alerts_active": await count(alerts_active_stmt),
        "watchlist_active": await count(select(WatchlistRow.id).where(WatchlistRow.active.is_(True))),
        "department_scope": user.department_id,
        "server_time": now.isoformat(),
    }


@router.get("/audit")
async def audit_log(
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin")),
):
    rows = (await session.execute(select(AuditRow).order_by(AuditRow.id.desc()).limit(min(limit, 500)))).scalars().all()
    return {"items": [
        {"ts": r.ts.isoformat(), "username": r.username, "action": r.action, "entity": r.entity, "details": r.details}
        for r in rows
    ]}
