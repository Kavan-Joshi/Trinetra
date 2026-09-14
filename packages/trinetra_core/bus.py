import asyncio
import json
import logging

import nats

from .config import settings

log = logging.getLogger("trinetra.bus")

STREAM = "TRINETRA"
SUBJECT_EVENTS = "trinetra.events.raw"
SUBJECT_ALERTS = "trinetra.alerts.new"
SUBJECT_WATCHLIST = "trinetra.watchlist.changed"
ALL_SUBJECTS = [SUBJECT_EVENTS, SUBJECT_ALERTS, SUBJECT_WATCHLIST]


async def connect(retries: int = 60, delay: float = 2.0):
    last_err = None
    for _ in range(retries):
        try:
            nc = await nats.connect(servers=[settings.nats_url], connect_timeout=3)
            js = nc.jetstream()
            try:
                await js.add_stream(name=STREAM, subjects=ALL_SUBJECTS, storage="file")
            except Exception:
                try:
                    await js.update_stream(name=STREAM, subjects=ALL_SUBJECTS)
                except Exception:
                    pass
            return nc, js
        except Exception as e:
            last_err = e
            log.warning("NATS connect failed (%s), retrying...", e)
            await asyncio.sleep(delay)
    raise ConnectionError(f"cannot reach NATS at {settings.nats_url}: {last_err}")


async def publish_json(js, subject: str, payload) -> None:
    data = payload if isinstance(payload, (str, bytes)) else payload.model_dump_json()
    if hasattr(data, "encode"):
        data = data.encode()
    await js.publish(subject, data)
