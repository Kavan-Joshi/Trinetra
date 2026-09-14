import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from trinetra_core.config import settings
from trinetra_core.db import init_db
from .auth import router as auth_router
from .routers.alerts import router as alerts_router
from .routers.community import router as community_router
from .routers.departments import router as departments_router
from .routers.events import router as events_router
from .routers.faces import router as faces_router
from .routers.gap_analysis import router as gap_analysis_router
from .routers.notifications import router as notifications_router
from .routers.records import router as records_router
from .routers.registry import router as registry_router
from .routers.watchlist import router as watchlist_router
from .ws import alert_broadcaster, router as ws_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trinetra.core-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    for attempt in range(60):
        try:
            await init_db()
            break
        except Exception as e:
            log.warning("db not ready (%s), retrying...", e)
            await asyncio.sleep(2)
    Path(settings.evidence_dir).mkdir(parents=True, exist_ok=True)
    task = asyncio.create_task(alert_broadcaster())
    yield
    task.cancel()


app = FastAPI(title="Trinetra Core API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Path(settings.evidence_dir).mkdir(parents=True, exist_ok=True)
app.mount("/evidence", StaticFiles(directory=settings.evidence_dir), name="evidence")

app.include_router(auth_router)
app.include_router(registry_router)
app.include_router(watchlist_router)
app.include_router(events_router)
app.include_router(alerts_router)
app.include_router(departments_router)
app.include_router(records_router)
app.include_router(faces_router)
app.include_router(gap_analysis_router)
app.include_router(community_router)
app.include_router(notifications_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "core-api"}
