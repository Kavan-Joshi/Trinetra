import asyncio
import logging

import bcrypt
from sqlalchemy import select

from trinetra_core.config import settings
from trinetra_core.db import AlertRow, AuditRow, CameraRow, DepartmentRow, EventRow, SessionLocal, User, WatchlistRow, init_db
from trinetra_core.plates import normalize_plate
from sim.data import CAMERAS, COMMUNITY_CAMERAS, DEPARTMENTS, WATCHLIST

log = logging.getLogger("trinetra.seed")

USERS = [
    ("admin", "admin123", "admin", "Command Administrator", None),
    ("operator", "operator123", "operator", "Control Room Operator", None),
    ("analyst", "analyst123", "analyst", "Crime Analyst", None),
    ("traffic", "traffic123", "operator", "Traffic Control Room", "traffic"),
    ("rto", "rto123", "operator", "RTO Office Operator", "rto"),
    ("fcs", "fcs123", "operator", "Food & Civil Supplies Operator", "fcs"),
]


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


async def seed() -> None:
    await init_db()
    async with SessionLocal() as s:
        dept_id_by_code: dict[str, int] = {}
        dept_id_by_name: dict[str, int] = {}
        for d in DEPARTMENTS:
            row = (await s.execute(select(DepartmentRow).where(DepartmentRow.code == d["code"]))).scalar_one_or_none()
            if row:
                row.name = d["name"]
                row.owner_contact = d.get("owner_contact", "")
                row.retention_events_days = d["retention_events_days"]
                row.retention_evidence_days = d["retention_evidence_days"]
            else:
                row = DepartmentRow(
                    code=d["code"], name=d["name"], owner_contact=d.get("owner_contact", ""),
                    retention_events_days=d["retention_events_days"], retention_evidence_days=d["retention_evidence_days"],
                )
                s.add(row)
            await s.flush()
            dept_id_by_code[d["code"]] = row.id
            dept_id_by_name[d["name"]] = row.id

        for username, pw, role, display, dept_code in USERS:
            user = (await s.execute(select(User).where(User.username == username))).scalar_one_or_none()
            dept_id = dept_id_by_code[dept_code] if dept_code else None
            if user:
                user.role, user.display_name, user.department_id = role, display, dept_id
            else:
                s.add(User(username=username, pw_hash=hash_pw(pw), role=role, display_name=display, department_id=dept_id))

        cams_new = cams_updated = 0
        if settings.seed_sim_cameras:
            all_cams = CAMERAS + COMMUNITY_CAMERAS
            for c in all_cams:
                row = await s.get(CameraRow, c["id"])
                dept_id = dept_id_by_name.get(c.get("department", ""))
                if row:
                    for k, v in c.items():
                        setattr(row, k, v)
                    row.department_id = dept_id
                    cams_updated += 1
                else:
                    row = CameraRow(**c)
                    row.department_id = dept_id
                    s.add(row)
                    cams_new += 1
        else:
            # live/grid mode: remove any previously-seeded sim cameras
            from sqlalchemy import delete as _delete
            sim_ids = [c["id"] for c in CAMERAS + COMMUNITY_CAMERAS]
            if sim_ids:
                await s.execute(_delete(EventRow).where(EventRow.camera_id.in_(sim_ids)))
                await s.execute(_delete(AlertRow).where(AlertRow.camera_id.in_(sim_ids)))
                await s.execute(_delete(CameraRow).where(CameraRow.id.in_(sim_ids)))
            log.info("seed_sim_cameras=False — %d sim cameras + their events/alerts removed", len(sim_ids))

        wl_new = 0
        for w in WATCHLIST:
            norm = normalize_plate(w.get("plate")) if w.get("plate") else None
            exists = (
                await s.execute(
                    select(WatchlistRow).where(
                        WatchlistRow.category == w["category"],
                        WatchlistRow.plate_norm == norm if norm else WatchlistRow.person_name == w.get("person_name"),
                    )
                )
            ).scalar_one_or_none()
            if exists:
                continue
            s.add(WatchlistRow(
                category=w["category"],
                plate_raw=w.get("plate"),
                plate_norm=norm,
                person_name=w.get("person_name"),
                description=w.get("description", ""),
                color=w.get("color"),
                model=w.get("model"),
                notes=w.get("notes", ""),
                created_by="seed",
                source_system="manual",
            ))
            wl_new += 1

        s.add(AuditRow(username="system", action="seed.run", entity="bootstrap",
                       details={"cameras_new": cams_new, "watchlist_new": wl_new, "departments": len(DEPARTMENTS)}))
        await s.commit()
    print(f"Seed complete: {len(DEPARTMENTS)} departments, {cams_new} new cameras ({cams_updated} updated), {wl_new} new watchlist entries, {len(USERS)} users.")


if __name__ == "__main__":
    asyncio.run(seed())
