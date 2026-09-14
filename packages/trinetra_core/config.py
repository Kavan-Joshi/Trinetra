from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRINETRA_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://trinetra:trinetra@postgres:5432/trinetra"
    nats_url: str = "nats://nats:4222"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    evidence_dir: str = "/data/evidence"
    sim_speed: float = 20.0
    session_gap_seconds: int = 3600
    alert_dedup_seconds: int = 60

    records_enabled: bool = True
    records_url: str = "http://records:8001"
    records_sync_interval_seconds: int = 300

    streamer_enabled: bool = True
    streamer_url: str = "http://streamer:8002"
    stream_token_ttl_seconds: int = 120

    notifier_enabled: bool = True
    notifier_webhook_url: str = "http://core-api:8000/api/v1/internal/webhook"

    retention_dry_run: bool = True
    retention_check_interval_seconds: int = 3600

    analytics_engine: str = "yolo_rapidocr"

    # When False, the seeder skips the 50 simulated cameras + community cameras
    # (use with the real grid — only cam01..cam30 remain, via the ingester).
    seed_sim_cameras: bool = True

    # Face recognition: cosine similarity threshold for a match (ArcFace).
    # Same person ~0.4-0.7; different person <0.35. Lower = more sensitive.
    face_match_threshold: float = 0.38

    # Face detection (InsightFace) — CPU-heavy. Set False for all-camera ANPR-only mode.
    face_detection: bool = True

    # External live camera grid (the provided CCTV feed infrastructure).
    # Credentials are injected via env — NEVER committed. email's '@' is
    # percent-encoded when embedded in rtsp/whep URLs.
    grid_catalogue_url: str = "https://cctv.corp8.cloud/cameras.json"
    grid_email: str = ""
    grid_password: str = ""
    grid_rtsp_host: str = "103.250.160.189:8554"
    grid_hls_base: str = "https://cctv.corp8.cloud"
    grid_whep_host: str = "103.250.160.189:8889"
    grid_default_lat: float = 23.0744
    grid_default_lon: float = 72.5169
    grid_department: str = "External Grid"


settings = Settings()
