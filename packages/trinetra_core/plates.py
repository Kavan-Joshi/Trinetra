import re

_PLATE_RE = re.compile(r"^([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{1,4})$")


def normalize_plate(raw: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (raw or "").upper())


def format_plate(norm: str | None) -> str:
    norm = norm or ""
    m = _PLATE_RE.match(norm)
    if not m:
        return norm
    return "-".join(p for p in m.groups() if p)


def plate_match(read: str | None, watchlist_plate: str | None) -> bool:
    return bool(read and watchlist_plate and normalize_plate(read) == normalize_plate(watchlist_plate))
