import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.bus import SUBJECT_WATCHLIST, connect, publish_json
from trinetra_core.db import WatchlistRow, get_session
from trinetra_core.plates import normalize_plate
from ..auth import audit, current_user, require_role

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])

CATEGORIES = {"stolen_vehicle", "blacklisted_vehicle", "wanted_person", "missing_person", "suspect"}

_bus: tuple | None = None


def wl_dict(r: WatchlistRow) -> dict:
    return {
        "id": r.id, "category": r.category, "plate": r.plate_raw, "plate_norm": r.plate_norm,
        "person_name": r.person_name, "description": r.description, "color": r.color,
        "model": r.model, "notes": r.notes, "active": r.active, "created_by": r.created_by,
        "source_system": r.source_system, "source_ref": r.source_ref,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


class WatchlistCreate(BaseModel):
    category: str
    plate: str | None = None
    person_name: str | None = None
    description: str = ""
    color: str | None = None
    model: str | None = None
    notes: str = ""
    source_system: str = "manual"
    source_ref: str | None = None


async def notify_watchlist_changed() -> None:
    global _bus
    if _bus is None:
        _bus = await connect(retries=3, delay=1.0)
    _, js = _bus
    await publish_json(js, SUBJECT_WATCHLIST, {"changed": True})


@router.get("")
async def list_watchlist(
    category: str | None = None,
    active: bool | None = None,
    q: str | None = None,
    limit: int = 200,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    stmt = select(WatchlistRow)
    if category:
        stmt = stmt.where(WatchlistRow.category == category)
    if active is not None:
        stmt = stmt.where(WatchlistRow.active == active)
    if q:
        norm = normalize_plate(q)
        stmt = stmt.where(or_(WatchlistRow.plate_norm.ilike(f"%{norm}%"), WatchlistRow.person_name.ilike(f"%{q}%")))
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
    rows = (await session.execute(stmt.order_by(WatchlistRow.id.desc()).offset(offset).limit(limit))).scalars().all()
    return {"total": total, "items": [wl_dict(r) for r in rows]}


@router.post("")
async def create_entry(
    entry: WatchlistCreate,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin", "analyst")),
):
    if entry.category not in CATEGORIES:
        raise HTTPException(422, f"category must be one of {sorted(CATEGORIES)}")
    row = WatchlistRow(
        category=entry.category,
        plate_raw=entry.plate,
        plate_norm=normalize_plate(entry.plate) if entry.plate else None,
        person_name=entry.person_name,
        description=entry.description,
        color=entry.color,
        model=entry.model,
        notes=entry.notes,
        created_by=user.username,
        source_system=entry.source_system,
        source_ref=entry.source_ref,
    )
    session.add(row)
    await audit(session, user.username, "watchlist.create", str(row.id), entry.model_dump())
    await session.commit()
    await notify_watchlist_changed()
    return wl_dict(row)


@router.delete("/{entry_id}")
async def deactivate_entry(
    entry_id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin", "analyst")),
):
    row = await session.get(WatchlistRow, entry_id)
    if not row:
        raise HTTPException(404, "entry not found")
    row.active = False
    await audit(session, user.username, "watchlist.deactivate", str(entry_id), {})
    await session.commit()
    await notify_watchlist_changed()
    return {"ok": True, "id": entry_id, "active": False}


@router.post("/import")
async def import_entries(request: Request, session: AsyncSession = Depends(get_session), user=Depends(require_role("admin", "analyst"))):
    body = await request.body()
    text = body.decode("utf-8-sig")
    entries: list[dict] = []
    ctype = request.headers.get("content-type", "")
    if "json" in ctype or text.strip().startswith("["):
        entries = json.loads(text)
    else:
        entries = list(csv.DictReader(io.StringIO(text)))
    imported = skipped = 0
    for raw in entries:
        category = (raw.get("category") or "").strip()
        if category not in CATEGORIES:
            skipped += 1
            continue
        plate = (raw.get("plate") or "").strip() or None
        session.add(WatchlistRow(
            category=category,
            plate_raw=plate,
            plate_norm=normalize_plate(plate) if plate else None,
            person_name=(raw.get("person_name") or "").strip() or None,
            description=(raw.get("description") or "").strip(),
            color=(raw.get("color") or "").strip() or None,
            model=(raw.get("model") or "").strip() or None,
            notes=(raw.get("notes") or "").strip(),
            created_by=user.username,
            source_system=(raw.get("source_system") or "manual").strip(),
            source_ref=(raw.get("source_ref") or "").strip() or None,
        ))
        imported += 1
    await audit(session, user.username, "watchlist.import", "watchlist", {"imported": imported, "skipped": skipped})
    await session.commit()
    if imported:
        await notify_watchlist_changed()
    return {"imported": imported, "skipped": skipped}
