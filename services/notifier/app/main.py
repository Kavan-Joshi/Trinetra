"""Alert fan-out service (Workstream 5).

Subscribes to ``trinetra.alerts.new`` and routes each alert to one or more
channels (SMS / email / webhook / FCM mobile push) per a category-based routing
table. Every dispatch is recorded as a NotificationRow so the operator console
can show a "Notifications" panel. SMS/email/FCM are mock-dispatched (logged) for
the demo; the webhook channel performs a real HTTP POST to the configured
endpoint so judges can observe end-to-end fan-out. Real gateways drop in behind
the dispatch() functions.
"""

import asyncio
import json
import logging
import urllib.request
from datetime import datetime, timezone

from pydantic import ValidationError

from trinetra_core.bus import SUBJECT_ALERTS, connect
from trinetra_core.config import settings
from trinetra_core.db import NotificationRow, SessionLocal, init_db
from trinetra_core.models import AlertPayload

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trinetra.notifier")

ROUTING: dict[str, list[dict]] = {
    "stolen_vehicle": [
        {"channel": "sms", "recipient": "DCP Control — stolen vehicle desk"},
        {"channel": "webhook", "recipient": "CCTNS/eGujCop"},
        {"channel": "fcm", "recipient": "field-units:traffic"},
    ],
    "blacklisted_vehicle": [
        {"channel": "webhook", "recipient": "CCTNS/eGujCop"},
        {"channel": "fcm", "recipient": "field-units:traffic"},
    ],
    "wanted_person": [
        {"channel": "sms", "recipient": "Crime Branch — wanted persons desk"},
        {"channel": "email", "recipient": "ci-crimebranch@gujpolice.gov.in"},
        {"channel": "webhook", "recipient": "CCTNS/eGujCop"},
        {"channel": "fcm", "recipient": "field-units:crime"},
    ],
    "missing_person": [
        {"channel": "sms", "recipient": "Missing Persons Bureau"},
        {"channel": "email", "recipient": "missing-persons@gujpolice.gov.in"},
        {"channel": "fcm", "recipient": "field-units:all"},
    ],
    "suspect": [
        {"channel": "sms", "recipient": "Local PS — suspect alert"},
        {"channel": "webhook", "recipient": "CCTNS/eGujCop"},
    ],
    "anomaly": [
        {"channel": "email", "recipient": "local-ps-alerts@gujpolice.gov.in"},
        {"channel": "fcm", "recipient": "field-units:local"},
    ],
}


async def _dispatch_webhook(payload: dict) -> bool:
    """Real HTTP POST to the configured webhook endpoint (best-effort)."""
    url = settings.notifier_webhook_url
    if not url:
        return False

    def _post() -> bool:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300

    try:
        return await asyncio.to_thread(_post)
    except Exception as e:
        log.warning("webhook dispatch to %s failed: %s", url, e)
        return False


async def _dispatch(channel: str, recipient: str, alert: AlertPayload) -> str:
    """Return 'sent' on success, 'failed' otherwise. Mock for sms/email/fcm."""
    if channel == "webhook":
        ok = await _dispatch_webhook(alert.model_dump())
        return "sent" if ok else "failed"
    # sms / email / fcm are mock-dispatched (logged) for the demo
    log.info("[%s] -> %s : %s", channel.upper(), recipient, alert.title)
    return "sent"


async def _handle_alert(alert: AlertPayload) -> None:
    rules = ROUTING.get(alert.category, [])
    rows = []
    for rule in rules:
        status = await _dispatch(rule["channel"], rule["recipient"], alert)
        rows.append(NotificationRow(
            alert_id=alert.alert_id, channel=rule["channel"], recipient=rule["recipient"],
            category=alert.category, title=alert.title,
            payload={"plate": alert.plate, "camera_id": alert.camera_id, "ts": alert.ts.isoformat(),
                     "source_system": alert.source_system, "source_ref": alert.source_ref},
            status=status,
        ))
    if rows:
        async with SessionLocal() as session:
            for r in rows:
                session.add(r)
            await session.commit()
        log.info("alert %s (%s) fanned out to %d channel(s)", alert.alert_id, alert.category, len(rows))


async def main() -> None:
    for attempt in range(60):
        try:
            await init_db()
            break
        except Exception as e:
            log.warning("db not ready (%s), retrying...", e)
            await asyncio.sleep(2)
    nc, _ = await connect()
    sub = await nc.subscribe(SUBJECT_ALERTS)
    log.info("notifier online — subscribed to %s", SUBJECT_ALERTS)

    async for msg in sub.messages:
        try:
            alert = AlertPayload.model_validate_json(msg.data)
            if alert.ts.tzinfo is None:
                alert.ts = alert.ts.replace(tzinfo=timezone.utc)
            await _handle_alert(alert)
        except ValidationError as e:
            log.warning("dropping malformed alert: %s", e)
        except Exception:
            log.exception("error handling alert")


if __name__ == "__main__":
    asyncio.run(main())
