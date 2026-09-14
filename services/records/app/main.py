import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Query
from sqlalchemy import or_, select

from trinetra_core.bus import SUBJECT_WATCHLIST, connect, publish_json
from trinetra_core.config import settings
from trinetra_core.db import SessionLocal, WatchlistRow, init_db
from trinetra_core.plates import normalize_plate
from trinetra_core.records import mock_enricher

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trinetra.records")

enricher = mock_enricher()
_bus: tuple | None = None


async def _notify_watchlist_changed() -> None:
    global _bus
    if _bus is None:
        _bus = await connect(retries=10, delay=2.0)
    _, js = _bus
    await publish_json(js, SUBJECT_WATCHLIST, {"changed": True, "source": "cctns"})


async def sync_cctns_feed() -> dict:
    """Upsert CCTNS-sourced records into the watchlist (auto-population)."""
    feed = await enricher.cctns_feed()
    created = updated = 0
    async with SessionLocal() as session:
        for entry in feed:
            norm = normalize_plate(entry.get("plate")) if entry.get("plate") else None
            stmt = select(WatchlistRow).where(WatchlistRow.category == entry["category"])
            if norm:
                stmt = stmt.where(WatchlistRow.plate_norm == norm)
            else:
                stmt = stmt.where(WatchlistRow.person_name == entry.get("person_name"))
            row = (await session.execute(stmt)).scalar_one_or_none()
            now = datetime.now(timezone.utc)
            if row is None:
                session.add(WatchlistRow(
                    category=entry["category"],
                    plate_raw=entry.get("plate"),
                    plate_norm=norm,
                    person_name=entry.get("person_name"),
                    description=entry.get("description", ""),
                    color=entry.get("color"),
                    model=entry.get("model"),
                    notes=entry.get("notes", ""),
                    created_by="cctns-sync",
                    source_system=entry.get("source_system", "cctns"),
                    source_ref=entry.get("source_ref"),
                    last_synced_at=now,
                    active=True,
                ))
                created += 1
            else:
                row.source_system = entry.get("source_system", "cctns")
                row.source_ref = entry.get("source_ref")
                row.last_synced_at = now
                row.description = entry.get("description", row.description)
                row.color = entry.get("color") or row.color
                row.model = entry.get("model") or row.model
                row.active = True
                updated += 1
        await session.commit()
    await _notify_watchlist_changed()
    log.info("CCTNS sync complete: %d created, %d updated", created, updated)
    return {"created": created, "updated": updated, "total_feed": len(feed)}


async def _sync_loop() -> None:
    await asyncio.sleep(5)
    while True:
        try:
            await sync_cctns_feed()
        except Exception:
            log.exception("CCTNS sync loop failed")
        await asyncio.sleep(settings.records_sync_interval_seconds)


app = FastAPI(title="Trinetra Records Service", version="1.0.0")


@app.on_event("startup")
async def _startup() -> None:
    for attempt in range(60):
        try:
            await init_db()
            break
        except Exception as e:
            log.warning("db not ready (%s), retrying...", e)
            await asyncio.sleep(2)
    asyncio.create_task(_sync_loop())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "records"}


@app.post("/records/sync")
async def trigger_sync():
    return await sync_cctns_feed()


@app.get("/records/plate/{plate}")
async def plate_dossier(plate: str):
    return await enricher.lookup_plate(plate)


@app.get("/records/person")
async def person_dossier(name: str = Query(...)):
    return await enricher.enrich_person(name)
