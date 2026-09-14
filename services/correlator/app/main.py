import asyncio
import json
import logging
import math
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from pydantic import ValidationError
from sqlalchemy import select

from trinetra_core.bus import SUBJECT_ALERTS, SUBJECT_EVENTS, connect, publish_json
from trinetra_core.config import settings
from trinetra_core.db import AlertRow, EventRow, SessionLocal, TrackRow, camera_by_id, init_db
from trinetra_core.models import AlertPayload, DetectionEvent
from trinetra_core.plates import format_plate, normalize_plate
from trinetra_core.records import mock_enricher
from trinetra_core.trajectory import same_session
from .matcher import WatchlistCache

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trinetra.correlator")

CATEGORY_LABELS = {
    "stolen_vehicle": "STOLEN VEHICLE",
    "blacklisted_vehicle": "BLACKLISTED VEHICLE",
    "wanted_person": "WANTED PERSON",
    "missing_person": "MISSING PERSON",
    "suspect": "SUSPECT",
}

wl = WatchlistCache()
enricher = mock_enricher()
redis: aioredis.Redis | None = None
js = None


def build_match_alert(alert_id, cam, ev, norm, entry, enrichment=None) -> tuple[AlertRow, AlertPayload]:
    label = CATEGORY_LABELS.get(entry.category, entry.category.upper())
    display = format_plate(norm)
    title = f"{label} DETECTED: {display} at {cam.name}"
    description = " | ".join(x for x in [entry.description, entry.notes] if x)
    if entry.model or entry.color:
        description = f"Vehicle: {entry.color or '?'} {entry.model or '?'} — {description}"
    confidence = ev.plate_confidence or 0.9
    common = dict(
        watchlist_id=entry.id,
        category=entry.category,
        title=title,
        plate=display,
        description=description,
        camera_id=ev.camera_id,
        ts=ev.ts,
        confidence=confidence,
        lat=cam.lat,
        lon=cam.lon,
        snapshot_path=ev.snapshot_path,
        source_system=entry.source_system,
        source_ref=entry.source_ref,
        enrichment=enrichment or {},
    )
    row = AlertRow(alert_id=uuid.UUID(alert_id), event_id=uuid.UUID(ev.event_id), **common)
    payload = AlertPayload(alert_id=alert_id, event_id=ev.event_id, camera_name=cam.name, **common)
    return row, payload


def build_anomaly_alert(alert_id, cam, ev) -> tuple[AlertRow, AlertPayload]:
    anomaly_type = ev.attributes.get("anomaly_type", "anomaly")
    title = f"ANOMALY ({anomaly_type.upper()}) at {cam.name}"
    confidence = float(ev.attributes.get("anomaly_confidence", 0.8))
    common = dict(
        watchlist_id=None,
        category="anomaly",
        title=title,
        plate=None,
        description=ev.attributes.get("anomaly_detail", ""),
        camera_id=ev.camera_id,
        ts=ev.ts,
        confidence=confidence,
        lat=cam.lat,
        lon=cam.lon,
        snapshot_path=ev.snapshot_path,
    )
    row = AlertRow(alert_id=uuid.UUID(alert_id), event_id=uuid.UUID(ev.event_id), **common)
    payload = AlertPayload(alert_id=alert_id, event_id=ev.event_id, camera_name=cam.name, **common)
    return row, payload


def build_face_alert(alert_id, cam, ev, matched_name, match_score, person_dossier) -> tuple[AlertRow, AlertPayload]:
    """Face-recognition alert: a detected face matched an enrolled gallery face."""
    cctns = person_dossier.get("cctns") or {}
    category = cctns.get("category", "wanted_person")
    label = CATEGORY_LABELS.get(category, category.upper())
    title = f"{label} DETECTED (face match): {matched_name} at {cam.name}"
    fir_ref = cctns.get("source_ref") or (person_dossier.get("nafis") or {}).get("fir_ref")
    common = dict(
        watchlist_id=None,
        category=category,
        title=title,
        plate=None,
        description=f"Face match (cosine {match_score:.0%}) — {cctns.get('description', '')}".strip(" —"),
        camera_id=ev.camera_id,
        ts=ev.ts,
        confidence=match_score,
        lat=cam.lat,
        lon=cam.lon,
        snapshot_path=ev.snapshot_path,
        source_system="face_recognition",
        source_ref=fir_ref,
        enrichment=person_dossier,
    )
    row = AlertRow(alert_id=uuid.UUID(alert_id), event_id=uuid.UUID(ev.event_id), **common)
    payload = AlertPayload(alert_id=alert_id, event_id=ev.event_id, camera_name=cam.name, **common)
    return row, payload


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two face embeddings (ArcFace 512-d)."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


async def on_event(msg) -> None:
    try:
        ev = DetectionEvent.model_validate_json(msg.data)
    except ValidationError as e:
        log.warning("dropping malformed event: %s", e)
        await msg.term()
        return
    if ev.ts.tzinfo is None:
        ev.ts = ev.ts.replace(tzinfo=timezone.utc)
    norm = normalize_plate(ev.plate_raw)
    payload: AlertPayload | None = None
    try:
        async with SessionLocal() as session:
            cam = await camera_by_id(session, ev.camera_id)
            if not cam:
                log.warning("event from unknown camera %s, dropping", ev.camera_id)
                await msg.ack()
                return
            event_uuid = uuid.UUID(ev.event_id)
            session.add(EventRow(
                event_id=event_uuid,
                camera_id=ev.camera_id,
                ts=ev.ts,
                kind=ev.kind,
                plate_raw=ev.plate_raw,
                plate_norm=norm or None,
                plate_confidence=ev.plate_confidence,
                vehicle_class=ev.vehicle_class,
                color=ev.color,
                direction=ev.direction,
                speed_kmh=ev.speed_kmh,
                bbox=ev.bbox,
                attributes=ev.attributes,
                snapshot_path=ev.snapshot_path,
            ))
            if norm:
                last = (
                    await session.execute(
                        select(TrackRow).where(TrackRow.plate_norm == norm).order_by(TrackRow.ts.desc()).limit(1)
                    )
                ).scalars().first()
                if last and same_session(last.ts, ev.ts):
                    session_id = last.session_id
                else:
                    session_id = str(uuid.uuid4())
                session.add(TrackRow(
                    plate_norm=norm, session_id=session_id, camera_id=ev.camera_id,
                    ts=ev.ts, lat=cam.lat, lon=cam.lon, event_id=event_uuid,
                ))
                entry = wl.plates.get(norm)
                if entry is not None:
                    dedup_key = f"trinetra:dedup:{entry.id}:{ev.camera_id}"
                    if await redis.set(dedup_key, "1", ex=settings.alert_dedup_seconds, nx=True):
                        alert_id = str(uuid.uuid4())
                        enrichment = await enricher.enrich_plate(norm)
                        row, payload = build_match_alert(alert_id, cam, ev, norm, entry, enrichment=enrichment)
                        session.add(row)
            if payload is None and ev.attributes.get("anomaly"):
                dedup_key = f"trinetra:dedup:anom:{ev.camera_id}"
                if await redis.set(dedup_key, "1", ex=600, nx=True):
                    alert_id = str(uuid.uuid4())
                    row, payload = build_anomaly_alert(alert_id, cam, ev)
                    session.add(row)
            # face recognition: compare the detected face embedding against the
            # enrolled face gallery in Redis (cosine similarity). No match -> no
            # alert (eliminates the previous false "always-Rahil-Shaikh" behaviour).
            if payload is None and ev.kind == "person" and ev.attributes.get("face"):
                embedding = ev.attributes.get("embedding")
                if embedding:
                    gallery = await redis.hgetall("trinetra:face_gallery")
                    best_name, best_score = None, 0.0
                    for gname, emb_json in gallery.items():
                        try:
                            gemb = json.loads(emb_json)
                            score = _cosine_similarity(embedding, gemb)
                            if score > best_score:
                                best_name, best_score = gname, score
                        except Exception:
                            continue
                    FACE_MATCH_THRESHOLD = settings.face_match_threshold
                    if best_name and best_score >= FACE_MATCH_THRESHOLD:
                        dedup_key = f"trinetra:dedup:face:{ev.camera_id}:{best_name}"
                        if await redis.set(dedup_key, "1", ex=600, nx=True):
                            person_dossier = await enricher.enrich_person(best_name)
                            log.info("FACE MATCH %s (%.0f%%) at %s", best_name, best_score * 100, ev.camera_id)
                            alert_id = str(uuid.uuid4())
                            row, payload = build_face_alert(alert_id, cam, ev, best_name, best_score, person_dossier)
                            session.add(row)
                    else:
                        log.debug("face detected (no gallery match, best=%.2f)", best_score)
            await session.commit()
        if payload is not None:
            await publish_json(js, SUBJECT_ALERTS, payload)
            log.info("ALERT %s | %s | cam %s", payload.category, payload.title, payload.camera_id)
        await redis.incr("trinetra:stats:events_processed")
        await msg.ack()
    except Exception:
        log.exception("error processing event %s", ev.event_id)
        try:
            await msg.nak(delay=2)
        except Exception:
            pass


async def main() -> None:
    global redis, js
    for attempt in range(60):
        try:
            await init_db()
            break
        except Exception as e:
            log.warning("db not ready (%s), retrying...", e)
            await asyncio.sleep(2)
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    cache_task = asyncio.create_task(wl.run())
    nc, js = await connect()
    await js.subscribe(SUBJECT_EVENTS, durable="trinetra-correlator", cb=on_event, manual_ack=True)
    log.info("correlator online — consuming %s", SUBJECT_EVENTS)
    try:
        await asyncio.Future()
    finally:
        cache_task.cancel()
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
