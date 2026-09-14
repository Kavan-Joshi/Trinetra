from datetime import datetime


def same_session(prev_ts: datetime, ts: datetime, gap_seconds: int | None = None) -> bool:
    if gap_seconds is None:
        from .config import settings

        gap_seconds = settings.session_gap_seconds
    delta = (ts - prev_ts).total_seconds()
    return 0 <= delta <= gap_seconds
