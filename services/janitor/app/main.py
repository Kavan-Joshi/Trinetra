import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select

from trinetra_core.config import settings
from trinetra_core.db import CameraRow, DepartmentRow, EventRow, SessionLocal, init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trinetra.janitor")


async def retention_pass() -> None:
    now = datetime.now(timezone.utc)
    async with SessionLocal() as session:
        depts = (await session.execute(select(DepartmentRow).order_by(DepartmentRow.id))).scalars().all()
        for d in depts:
            cutoff = now - timedelta(days=d.retention_events_days)
            cam_ids = select(CameraRow.id).where(CameraRow.department_id == d.id)
            stmt = select(EventRow.id).where(EventRow.camera_id.in_(cam_ids), EventRow.ts < cutoff)
            count = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
            if not count:
                continue
            action = "would purge" if settings.retention_dry_run else "purging"
            log.info("retention[%s|%s]: %s %d event(s) older than %d day(s) [cutoff %s]",
                     d.code, d.name, action, count, d.retention_events_days, cutoff.isoformat())
            if not settings.retention_dry_run:
                await session.execute(delete(EventRow).where(
                    EventRow.camera_id.in_(cam_ids), EventRow.ts < cutoff
                ))
                await session.commit()


async def main() -> None:
    for attempt in range(60):
        try:
            await init_db()
            break
        except Exception as e:
            log.warning("db not ready (%s), retrying...", e)
            await asyncio.sleep(2)
    log.info("janitor online — dry_run=%s interval=%ss",
             settings.retention_dry_run, settings.retention_check_interval_seconds)
    while True:
        try:
            await retention_pass()
        except Exception:
            log.exception("retention pass failed")
        await asyncio.sleep(settings.retention_check_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
