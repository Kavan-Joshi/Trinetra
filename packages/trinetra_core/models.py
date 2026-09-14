from datetime import date, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Camera(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    vendor: str = "Unknown"
    vms: str = "Standalone NVR"
    protocol: str = "rtsp"
    status: str = "online"
    department: str = "Surveillance Cell"
    zone: str = "Zone-1"
    stream_url: str = ""
    direction: str = ""
    department_id: int | None = None
    source_type: str = "gov"
    consent: bool = False
    install_date: date | None = None
    health: str = "healthy"
    maintenance_status: str = "ok"
    coverage_radius_m: int = 80
    firmware: str = ""


class DetectionEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    camera_id: str
    ts: datetime
    kind: str = "vehicle"
    plate_raw: str | None = None
    plate_confidence: float | None = None
    vehicle_class: str | None = None
    color: str | None = None
    direction: str | None = None
    speed_kmh: float | None = None
    bbox: list[int] | None = None
    attributes: dict = Field(default_factory=dict)
    snapshot_path: str | None = None


class AlertPayload(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    event_id: str
    watchlist_id: int | None = None
    category: str
    title: str
    plate: str | None = None
    description: str = ""
    camera_id: str
    camera_name: str = ""
    ts: datetime
    confidence: float
    lat: float
    lon: float
    snapshot_path: str | None = None
    source_system: str = "manual"
    source_ref: str | None = None
    enrichment: dict = Field(default_factory=dict)


class WatchlistIn(BaseModel):
    category: str
    plate: str | None = None
    person_name: str | None = None
    description: str = ""
    color: str | None = None
    model: str | None = None
    notes: str = ""
    active: bool = True
    source_system: str = "manual"
    source_ref: str | None = None


class Department(BaseModel):
    id: int | None = None
    code: str
    name: str
    owner_contact: str = ""
    retention_events_days: int = 30
    retention_evidence_days: int = 90


class VehicleRecord(BaseModel):
    plate_norm: str
    plate_display: str
    owner_name: str | None = None
    make: str | None = None
    model: str | None = None
    color: str | None = None
    vehicle_class: str | None = None
    fitness_expiry: str | None = None
    insurance_valid: bool | None = None
    source_system: str = "vahan"
    source_ref: str | None = None


class PersonRecord(BaseModel):
    person_name: str | None = None
    category: str | None = None
    fir_ref: str | None = None
    description: str = ""
    source_system: str = "cctns"
    source_ref: str | None = None


class FingerprintMatch(BaseModel):
    matched: bool
    score: float = 0.0
    person_name: str | None = None
    fir_ref: str | None = None
    source_system: str = "nafis"
    source_ref: str | None = None


class CommunityCameraIn(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    stream_url: str
    owner_name: str = ""
    owner_contact: str = ""
    consent: bool = True
    notes: str = ""


class TrackPoint(BaseModel):
    camera_id: str
    camera_name: str
    ts: datetime
    lat: float
    lon: float
    snapshot_path: str | None = None


class TrackSession(BaseModel):
    session_id: str
    points: list[TrackPoint]


class RouteResponse(BaseModel):
    plate: str
    display_plate: str
    sessions: list[TrackSession]
