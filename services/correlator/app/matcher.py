import asyncio
import logging

from sqlalchemy import select

from trinetra_core.bus import SUBJECT_WATCHLIST, connect
from trinetra_core.db import SessionLocal, WatchlistRow

log = logging.getLogger("trinetra.matcher")


class WatchlistCache:
    def __init__(self):
        self.plates: dict[str, WatchlistRow] = {}

    async def refresh(self) -> None:
        async with SessionLocal() as session:
            rows = (
                await session.execute(
                    select(WatchlistRow).where(WatchlistRow.active.is_(True), WatchlistRow.plate_norm.isnot(None))
                )
            ).scalars().all()
        self.plates = {r.plate_norm: r for r in rows}
        log.info("watchlist cache refreshed: %d active plate entries", len(self.plates))

    async def run(self) -> None:
        nc, _ = await connect()
        sub = await nc.subscribe(SUBJECT_WATCHLIST)
        await self.refresh()

        async def on_change() -> None:
            async for _msg in sub.messages:
                await self.refresh()

        async def periodic() -> None:
            while True:
                await asyncio.sleep(10)
                await self.refresh()

        await asyncio.gather(on_change(), periodic())
