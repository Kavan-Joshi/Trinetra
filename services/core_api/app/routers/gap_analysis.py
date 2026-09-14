import csv
import io
import math
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.db import CameraRow, get_session
from ..auth import current_user

router = APIRouter(prefix="/api/v1/gap-analysis", tags=["gap-analysis"])

# indicative planning targets (configurable in production)
MIN_ONLINE_PER_ZONE = 6
MIN_ONLINE_RATIO = 0.6
MIN_COVERAGE_KM2 = 0.30
AGEING_YEARS = 5
CRITICAL_YEARS = 7


@router.get("/coverage")
async def coverage_gaps(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    """Per-zone coverage assessment: camera counts, health, estimated coverage
    footprint, and a gap flag where online density falls below planning targets.
    """
    rows = (await session.execute(select(CameraRow))).scalars().all()
    by_zone: dict[str, dict] = {}
    for c in rows:
        z = c.zone or "Unzoned"
        d = by_zone.setdefault(z, {"zone": z, "total": 0, "online": 0, "degraded": 0,
                                   "offline": 0, "in_repair": 0, "coverage_m2": 0.0,
                                   "departments": set()})
        d["total"] += 1
        if c.status == "online" and c.health != "offline":
            d["online"] += 1
        if c.health == "degraded":
            d["degraded"] += 1
        if c.health == "offline" or c.status == "offline":
            d["offline"] += 1
        if c.maintenance_status == "in_repair":
            d["in_repair"] += 1
        d["coverage_m2"] += math.pi * (c.coverage_radius_m or 80) ** 2
        if c.department:
            d["departments"].add(c.department)

    items = []
    for d in by_zone.values():
        d["departments"] = sorted(d["departments"])
        d["coverage_km2"] = round(d.pop("coverage_m2") / 1_000_000, 3)
        d["online_ratio"] = round(d["online"] / d["total"], 2) if d["total"] else 0
        d["gap"] = (
            d["online"] < MIN_ONLINE_PER_ZONE
            or d["online_ratio"] < MIN_ONLINE_RATIO
            or d["coverage_km2"] < MIN_COVERAGE_KM2
        )
        items.append(d)
    items.sort(key=lambda x: x["zone"])
    gaps = [i for i in items if i["gap"]]
    return {"total_zones": len(items), "zones_with_gaps": len(gaps), "items": items}


@router.get("/ageing")
async def ageing_infrastructure(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    """Ageing-infrastructure assessment: cameras grouped by age bucket, end-of-life
    firmware, and those needing maintenance/replacement.
    """
    today = date.today()
    rows = (await session.execute(select(CameraRow))).scalars().all()
    buckets = {"under_2y": [], "2_to_5y": [], "5_to_7y": [], "over_7y": []}
    eol_firmware: list[dict] = []
    maintenance_issues: list[dict] = []
    for c in rows:
        age = (today - c.install_date).days / 365.25 if c.install_date else 0
        entry = {"id": c.id, "name": c.name, "zone": c.zone, "vendor": c.vendor,
                 "department": c.department, "install_date": c.install_date.isoformat() if c.install_date else None,
                 "age_years": round(age, 1), "firmware": c.firmware,
                 "health": c.health, "maintenance_status": c.maintenance_status}
        if age >= CRITICAL_YEARS:
            buckets["over_7y"].append(entry)
        elif age >= AGEING_YEARS:
            buckets["5_to_7y"].append(entry)
        elif age >= 2:
            buckets["2_to_5y"].append(entry)
        else:
            buckets["under_2y"].append(entry)
        if c.firmware and c.firmware.startswith("v2"):
            eol_firmware.append(entry)
        if c.maintenance_status != "ok" or c.health not in ("healthy",):
            maintenance_issues.append(entry)
    return {
        "ageing_threshold_years": AGEING_YEARS,
        "critical_threshold_years": CRITICAL_YEARS,
        "buckets": {k: v for k, v in buckets.items()},
        "counts": {k: len(v) for k, v in buckets.items()},
        "eol_firmware_count": len(eol_firmware),
        "maintenance_issue_count": len(maintenance_issues),
        "eol_firmware": eol_firmware,
        "maintenance_issues": maintenance_issues,
    }


@router.get("/report")
async def full_report(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    """Combined gap-analysis report (the Model-1 sample deliverable)."""
    cov = await coverage_gaps(session, user)
    age = await ageing_infrastructure(session, user)
    total = cov["total_zones"]
    gaps = cov["zones_with_gaps"]
    ageing_count = age["counts"]["5_to_7y"] + age["counts"]["over_7y"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "zones_assessed": total,
            "zones_with_coverage_gaps": gaps,
            "ageing_cameras": ageing_count,
            "critical_cameras_over_7y": age["counts"]["over_7y"],
            "end_of_life_firmware": age["eol_firmware_count"],
            "cameras_needing_maintenance": age["maintenance_issue_count"],
        },
        "coverage": cov,
        "ageing": age,
        "recommendations": _recommendations(cov, age),
    }


@router.get("/report/download")
async def download_report(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    """Download the gap-analysis report as CSV (zone-level coverage + ageing summary)."""
    cov = await coverage_gaps(session, user)
    age = await ageing_infrastructure(session, user)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["TRINETRA GAP-ANALYSIS REPORT"])
    w.writerow(["Generated", datetime.now(timezone.utc).isoformat()])
    w.writerow([])
    w.writerow(["SECTION 1 — COVERAGE BY ZONE"])
    w.writerow(["Zone", "Total cameras", "Online", "Degraded", "Offline", "In repair",
                "Coverage km2", "Online ratio", "Coverage gap"])
    for i in cov["items"]:
        w.writerow([i["zone"], i["total"], i["online"], i["degraded"], i["offline"],
                    i["in_repair"], i["coverage_km2"], i["online_ratio"], "YES" if i["gap"] else "no"])
    w.writerow([])
    w.writerow(["SECTION 2 — AGEING INFRASTRUCTURE"])
    w.writerow(["Bucket", "Count"])
    for k, v in age["counts"].items():
        w.writerow([k, v])
    w.writerow(["End-of-life firmware (v2.x)", age["eol_firmware_count"]])
    w.writerow(["Cameras needing maintenance", age["maintenance_issue_count"]])
    w.writerow([])
    w.writerow(["SECTION 3 — CAMERAS NEEDING REPLACEMENT / MAINTENANCE"])
    w.writerow(["Camera", "Zone", "Age years", "Firmware", "Health", "Maintenance"])
    for c in age["maintenance_issues"] + [x for x in age["buckets"]["over_7y"]]:
        w.writerow([c["id"], c["zone"], c["age_years"], c["firmware"], c["health"], c["maintenance_status"]])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trinetra-gap-analysis-report.csv"},
    )


def _recommendations(cov: dict, age: dict) -> list[str]:
    recs: list[str] = []
    gap_zones = [i["zone"] for i in cov["items"] if i["gap"]]
    if gap_zones:
        recs.append(f"Deploy additional cameras in {len(gap_zones)} under-covered zone(s): {', '.join(gap_zones)}.")
    if age["counts"]["over_7y"]:
        recs.append(f"Plan replacement of {age['counts']['over_7y']} camera(s) older than 7 years (end-of-life hardware).")
    if age["eol_firmware_count"]:
        recs.append(f"Upgrade firmware on {age['eol_firmware_count']} camera(s) running end-of-life v2.x firmware.")
    if age["maintenance_issue_count"]:
        recs.append(f"Schedule maintenance for {age['maintenance_issue_count']} camera(s) in degraded health or under repair.")
    if not recs:
        recs.append("No significant gaps or ageing issues detected at current thresholds.")
    return recs
