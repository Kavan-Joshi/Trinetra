import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, func, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import settings


class Base(DeclarativeBase):
    pass


class DepartmentRow(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    owner_contact: Mapped[str] = mapped_column(String(128), default="")
    retention_events_days: Mapped[int] = mapped_column(Integer, default=30)
    retention_evidence_days: Mapped[int] = mapped_column(Integer, default=90)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    pw_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(32), default="operator")
    display_name: Mapped[str] = mapped_column(String(128), default="")
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)


class CameraRow(Base):
    __tablename__ = "cameras"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    vendor: Mapped[str] = mapped_column(String(64), default="Unknown")
    vms: Mapped[str] = mapped_column(String(64), default="Standalone NVR")
    protocol: Mapped[str] = mapped_column(String(32), default="rtsp")
    status: Mapped[str] = mapped_column(String(16), default="online")
    department: Mapped[str] = mapped_column(String(64), default="Surveillance Cell")
    zone: Mapped[str] = mapped_column(String(32), default="Zone-1")
    stream_url: Mapped[str] = mapped_column(Text, default="")
    direction: Mapped[str] = mapped_column(String(64), default="")
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="gov")
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    install_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    health: Mapped[str] = mapped_column(String(16), default="healthy")
    maintenance_status: Mapped[str] = mapped_column(String(16), default="ok")
    coverage_radius_m: Mapped[int] = mapped_column(Integer, default=80)
    firmware: Mapped[str] = mapped_column(String(32), default="")
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class WatchlistRow(Base):
    __tablename__ = "watchlist"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    plate_norm: Mapped[str | None] = mapped_column(String(16), index=True)
    plate_raw: Mapped[str | None] = mapped_column(String(24))
    person_name: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    color: Mapped[str | None] = mapped_column(String(32))
    model: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_system: Mapped[str] = mapped_column(String(32), default="manual")
    source_ref: Mapped[str | None] = mapped_column(String(64))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(String(64), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class EventRow(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    camera_id: Mapped[str] = mapped_column(String(32), ForeignKey("cameras.id"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="vehicle")
    plate_raw: Mapped[str | None] = mapped_column(String(24))
    plate_norm: Mapped[str | None] = mapped_column(String(16))
    plate_confidence: Mapped[float | None] = mapped_column(Float)
    vehicle_class: Mapped[str | None] = mapped_column(String(32))
    color: Mapped[str | None] = mapped_column(String(32))
    direction: Mapped[str | None] = mapped_column(String(32))
    speed_kmh: Mapped[float | None] = mapped_column(Float)
    bbox: Mapped[dict | list | None] = mapped_column(JSONB)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    snapshot_path: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_events_plate_ts", "plate_norm", "ts"),)


class AlertRow(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(UUID(as_uuid=True))
    watchlist_id: Mapped[int | None] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(256))
    plate: Mapped[str | None] = mapped_column(String(24))
    description: Mapped[str] = mapped_column(Text, default="")
    camera_id: Mapped[str] = mapped_column(String(32))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    snapshot_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(64))
    source_system: Mapped[str] = mapped_column(String(32), default="manual")
    source_ref: Mapped[str | None] = mapped_column(String(64))
    enrichment: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class TrackRow(Base):
    __tablename__ = "tracks"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plate_norm: Mapped[str] = mapped_column(String(16))
    session_id: Mapped[str] = mapped_column(String(36))
    camera_id: Mapped[str] = mapped_column(String(32))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    event_id: Mapped[str] = mapped_column(UUID(as_uuid=True))

    __table_args__ = (Index("ix_tracks_plate_ts", "plate_norm", "ts"),)


class AuditRow(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    username: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict] = mapped_column(JSONB, default=dict)


class NotificationRow(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String(64), index=True)
    channel: Mapped[str] = mapped_column(String(16))
    recipient: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(256))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="sent")
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), index=True)


engine = create_async_engine(settings.database_url, pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in (
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS department_id INTEGER REFERENCES departments(id)",
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS source_type VARCHAR(16) DEFAULT 'gov'",
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS consent BOOLEAN DEFAULT FALSE",
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS install_date DATE",
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS health VARCHAR(16) DEFAULT 'healthy'",
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS maintenance_status VARCHAR(16) DEFAULT 'ok'",
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS coverage_radius_m INTEGER DEFAULT 80",
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS firmware VARCHAR(32) DEFAULT ''",
            "ALTER TABLE cameras ADD COLUMN IF NOT EXISTS last_heartbeat TIMESTAMPTZ",
            "ALTER TABLE watchlist ADD COLUMN IF NOT EXISTS source_system VARCHAR(32) DEFAULT 'manual'",
            "ALTER TABLE watchlist ADD COLUMN IF NOT EXISTS source_ref VARCHAR(64)",
            "ALTER TABLE watchlist ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS department_id INTEGER REFERENCES departments(id)",
            "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS source_system VARCHAR(32) DEFAULT 'manual'",
            "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS source_ref VARCHAR(64)",
            "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS enrichment JSONB DEFAULT '{}'::jsonb",
        ):
            await conn.execute(text(stmt))
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS notifications ("
            "id BIGSERIAL PRIMARY KEY, alert_id VARCHAR(64), channel VARCHAR(16), "
            "recipient VARCHAR(128), category VARCHAR(32), title VARCHAR(256), "
            "payload JSONB DEFAULT '{}'::jsonb, status VARCHAR(16) DEFAULT 'sent', "
            "ts TIMESTAMPTZ DEFAULT now())"
        ))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_ts ON notifications (ts)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_alert_id ON notifications (alert_id)"))


async def camera_by_id(session: AsyncSession, camera_id: str) -> CameraRow | None:
    return (await session.execute(select(CameraRow).where(CameraRow.id == camera_id))).scalar_one_or_none()
