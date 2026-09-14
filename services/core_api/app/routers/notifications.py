import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.db import NotificationRow, get_session
from ..auth import current_user

log = logging.getLogger("trinetra.webhook")
router = APIRouter(tags=["notifications"])


def notif_dict(r: NotificationRow) -> dict:
    return {
        "id": r.id, "alert_id": r.alert_id, "channel": r.channel, "recipient": r.recipient,
        "category": r.category, "title": r.title, "payload": r.payload, "status": r.status,
        "ts": r.ts.isoformat(),
    }


@router.get("/api/v1/notifications")
async def list_notifications(
    channel: str | None = None,
    category: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    stmt = select(NotificationRow)
    if channel:
        stmt = stmt.where(NotificationRow.channel == channel)
    if category:
        stmt = stmt.where(NotificationRow.category == category)
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
    rows = (await session.execute(stmt.order_by(NotificationRow.ts.desc()).limit(min(limit, 500)))).scalars().all()
    return {"total": total, "items": [notif_dict(r) for r in rows]}


@router.post("/api/v1/internal/webhook")
async def internal_webhook(request: Request):
    """Internal webhook sink for the notifier's CCTNS/eGujCop fan-out (demo).

    Receives alert payloads pushed by the notifier service and acknowledges them.
    In production this is the bridge into CCTNS/FIR systems; here it logs the
    receipt so the end-to-end fan-out is observable.
    """
    body = await request.body()
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": body.decode(errors="replace")[:500]}
    log.info("webhook receipt from notifier: %s", payload.get("title") or payload.get("alert_id") or "unknown")
    return {"status": "ok", "received": True}
