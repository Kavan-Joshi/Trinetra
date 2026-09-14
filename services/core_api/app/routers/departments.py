from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.db import CameraRow, DepartmentRow, EventRow, get_session
from ..auth import audit, current_user, require_role

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


def dept_dict(r: DepartmentRow, *, camera_count: int | None = None) -> dict:
    out = {
        "id": r.id, "code": r.code, "name": r.name, "owner_contact": r.owner_contact,
        "retention_events_days": r.retention_events_days,
        "retention_evidence_days": r.retention_evidence_days,
    }
    if camera_count is not None:
        out["camera_count"] = camera_count
    return out


class DepartmentPatch(BaseModel):
    owner_contact: str | None = None
    retention_events_days: int | None = None
    retention_evidence_days: int | None = None


@router.get("")
async def list_departments(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    rows = (await session.execute(select(DepartmentRow).order_by(DepartmentRow.id))).scalars().all()
    out = []
    for r in rows:
        cam_count = (await session.execute(
            select(func.count()).select_from(select(CameraRow.id).where(CameraRow.department_id == r.id).subquery())
        )).scalar()
        out.append(dept_dict(r, camera_count=cam_count))
    return {"total": len(out), "items": out}


@router.get("/{dept_id}")
async def get_department(dept_id: int, session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    row = await session.get(DepartmentRow, dept_id)
    if not row:
        raise HTTPException(404, "department not found")
    return dept_dict(row)


@router.patch("/{dept_id}")
async def patch_department(
    dept_id: int,
    patch: DepartmentPatch,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin")),
):
    row = await session.get(DepartmentRow, dept_id)
    if not row:
        raise HTTPException(404, "department not found")
    for k, v in patch.model_dump(exclude_none=True).items():
        setattr(row, k, v)
    await audit(session, user.username, "department.update", str(dept_id), patch.model_dump(exclude_none=True))
    await session.commit()
    return dept_dict(row)


@router.get("/retention/report")
async def retention_report(session: AsyncSession = Depends(get_session), user=Depends(require_role("admin", "analyst"))):
    """Dry-run retention report: per department, how many events would be purged.

    Honours ``settings.retention_dry_run`` — in dry-run mode (default) this only
    reports counts; the janitor service performs actual purge when dry-run is off.
    """
    from trinetra_core.config import settings

    now = datetime.now(timezone.utc)
    depts = (await session.execute(select(DepartmentRow).order_by(DepartmentRow.id))).scalars().all()
    rows = []
    total_purge = 0
    for d in depts:
        cutoff = now - timedelta(days=d.retention_events_days)
        cam_ids = select(CameraRow.id).where(CameraRow.department_id == d.id)
        purge_count = (await session.execute(
            select(func.count()).select_from(
                select(EventRow.id).where(EventRow.camera_id.in_(cam_ids), EventRow.ts < cutoff).subquery()
            )
        )).scalar()
        total_purge += purge_count
        rows.append({
            "department_id": d.id, "code": d.code, "name": d.name,
            "retention_events_days": d.retention_events_days,
            "retention_evidence_days": d.retention_evidence_days,
            "events_to_purge": purge_count, "cutoff": cutoff.isoformat(),
        })
    return {"dry_run": settings.retention_dry_run, "total_events_to_purge": total_purge, "items": rows}
