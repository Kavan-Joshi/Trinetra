import datetime as _dt

_COORDS = [
    (23.0100, 72.5450), (23.0141, 72.5434), (23.0182, 72.5417), (23.0223, 72.5401),
    (23.0263, 72.5385), (23.0304, 72.5368), (23.0345, 72.5352), (23.0386, 72.5343),
    (23.0427, 72.5335), (23.0467, 72.5327), (23.0508, 72.5318), (23.0549, 72.5310),
    (23.0590, 72.5302), (23.0631, 72.5306), (23.0672, 72.5314), (23.0712, 72.5322),
    (23.0753, 72.5331), (23.0794, 72.5339), (23.0835, 72.5347), (23.0870, 72.5365),
    (23.0903, 72.5390), (23.0936, 72.5414), (23.0968, 72.5439), (23.1001, 72.5463),
    (23.1034, 72.5488), (23.1071, 72.5521), (23.1111, 72.5561), (23.1152, 72.5602),
    (23.1193, 72.5643), (23.1234, 72.5684), (23.1275, 72.5725), (23.1324, 72.5765),
    (23.1390, 72.5806), (23.1455, 72.5847), (23.1520, 72.5888), (23.1586, 72.5929),
    (23.1651, 72.5969), (23.1716, 72.6012), (23.1782, 72.6061), (23.1847, 72.6110),
    (23.1912, 72.6159), (23.1978, 72.6208), (23.2043, 72.6257), (23.2104, 72.6304),
    (23.2137, 72.6337), (23.2169, 72.6369), (23.2202, 72.6402), (23.2235, 72.6435),
    (23.2267, 72.6467), (23.2300, 72.6500),
]

_NAMES = [
    "Nehru Bridge", "Ashram Road x Paldi", "Ashram Road x Ellisbridge", "Ashram Road x Gujarat College",
    "Ashram Road x Stadium Circle", "Ashram Road x Usmanpura", "Vadaj Circle",
    "Ring Road x Delhi Darwaja", "Ring Road x Income Tax", "Ring Road x Navrangpura",
    "Ring Road x Stadium", "Ring Road x Vijay Crossroad", "Delhi Darwaja Junction",
    "Navrangpura Char Rasta", "Law Garden Junction", "Stadium Circle",
    "Commerce Six Roads", "Vijay Crossroads", "Gujarat College Junction",
    "Drive-In Road x Shivranjani", "Drive-In Road x Helmet", "Vastrapur Lake Road",
    "Prahladnagar Garden", "SG Highway x Prahladnagar", "SG Highway x Shivranjani",
    "SG Highway x Panjarapole", "SG Highway x Iskcon", "SG Highway x Ramdev Nagar",
    "SG Highway x Bodakdev", "SG Highway x Thaltej", "SG Highway x Bopal Junction",
    "SP Ring Road x Shela", "SP Ring Road x Bodakdev West", "SP Ring Road x Gota",
    "SP Ring Road x Chandkheda", "SP Ring Road x Kudasan", "Sarkhej-Gandhinagar Connector",
    "Tragad Junction", "Chenpur Crossroad", "Zundal Circle",
    "SG Highway x Zundal", "Gandhinagar Highway x Kudasan", "Gandhinagar Highway x Infocity Approach",
    "Gandhinagar Sector 21 Entrance", "Infocity Circle", "Sector 16A Junction",
    "Sector 7 Junction", "Sector 1 Junction", "Sachivalaya Approach",
    "Gandhinagar Sachivalaya Gate",
]

_VENDORS = ["Hikvision", "CP Plus", "Dahua", "Axis Communications", "Bosch", "Pelco", "Honeywell", "Vivotek"]
_VMS = ["Milestone XProtect", "Genetec Security Center", "CP Plus VMS", "ExacqVision", "Digifort", "Standalone NVR"]
_PROTOCOLS = ["rtsp", "onvif", "http-mjpeg", "vendor-api", "gb28181"]

DEPARTMENTS = [
    {"code": "home", "name": "Home Department (Surveillance Cell)", "retention_events_days": 30, "retention_evidence_days": 90},
    {"code": "police_scr", "name": "Gujarat Police — State Control Room", "retention_events_days": 30, "retention_evidence_days": 90},
    {"code": "gsrtc", "name": "GSRTC (Gujarat State Road Transport)", "retention_events_days": 15, "retention_evidence_days": 60},
    {"code": "panchayat", "name": "Panchayat (Rural Development)", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "traffic", "name": "Traffic Police", "retention_events_days": 15, "retention_evidence_days": 60},
    {"code": "rto", "name": "Transport / RTO", "retention_events_days": 15, "retention_evidence_days": 60},
    {"code": "fcs", "name": "Food & Civil Supplies", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "ga", "name": "General Administration", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "ud", "name": "Urban Development (Municipalities)", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "revenue", "name": "Revenue Department", "retention_events_days": 7, "retention_evidence_days": 30},
    {"code": "hg_cd", "name": "Home Guards & Civil Defence", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "fire", "name": "Fire & Emergency Services", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "grp", "name": "Railway Police (GRP)", "retention_events_days": 30, "retention_evidence_days": 90},
    {"code": "ports", "name": "Ports & Transport", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "rnb", "name": "Roads & Buildings (R&B)", "retention_events_days": 7, "retention_evidence_days": 30},
    {"code": "energy", "name": "Energy / DISCOMs", "retention_events_days": 7, "retention_evidence_days": 30},
    {"code": "water", "name": "Water Resources / Narmada", "retention_events_days": 7, "retention_evidence_days": 30},
    {"code": "forest", "name": "Forest & Environment", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "tourism", "name": "Tourism", "retention_events_days": 7, "retention_evidence_days": 30},
    {"code": "sports", "name": "Sports, Youth & Cultural Affairs", "retention_events_days": 7, "retention_evidence_days": 30},
    {"code": "edu", "name": "Education (Schools & Colleges)", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "health", "name": "Health & Family Welfare (Hospitals)", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "wcd", "name": "Women & Child Development", "retention_events_days": 30, "retention_evidence_days": 90},
    {"code": "sje", "name": "Social Justice & Empowerment", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "industries", "name": "Industries / GIDC", "retention_events_days": 7, "retention_evidence_days": 30},
    {"code": "agri", "name": "Agriculture / APMC", "retention_events_days": 7, "retention_evidence_days": 30},
    {"code": "it_bt", "name": "Science & Technology / IT", "retention_events_days": 15, "retention_evidence_days": 45},
    {"code": "dmgsdma", "name": "Disaster Management / GSDMA", "retention_events_days": 30, "retention_evidence_days": 90},
]
_DEPARTMENTS = [d["name"] for d in DEPARTMENTS]

COMMUNITY_CAMERAS = [
    {
        "id": "COMM-001",
        "name": "Satyam Society Gate — Iscon",
        "lat": 23.0263, "lon": 72.5385,
        "vendor": "CP Plus", "vms": "Standalone NVR", "protocol": "rtsp",
        "status": "online", "department": "Community (Private)", "zone": "Zone-3 SG Highway",
        "stream_url": "rtsp://community-gw1.local:554/live/comm001",
        "direction": "Both", "source_type": "community", "consent": True,
    },
    {
        "id": "COMM-002",
        "name": "AlphaOne Mall Entrance — Vastrapur",
        "lat": 23.0368, "lon": 72.5290,
        "vendor": "Hikvision", "vms": "Standalone NVR", "protocol": "rtsp",
        "status": "online", "department": "Community (Private)", "zone": "Zone-2 Ahmedabad Central",
        "stream_url": "rtsp://community-gw2.local:554/live/comm002",
        "direction": "Both", "source_type": "community", "consent": True,
    },
    {
        "id": "COMM-003",
        "name": "Pallav Commercial Plaza — Prahladnagar",
        "lat": 23.0968, "lon": 72.5439,
        "vendor": "Dahua", "vms": "Standalone NVR", "protocol": "onvif",
        "status": "online", "department": "Community (Private)", "zone": "Zone-3 SG Highway",
        "stream_url": "rtsp://community-gw3.local:554/live/comm003",
        "direction": "Both", "source_type": "community", "consent": True,
    },
]
OFFLINE_INDICES = {4, 22, 38}


def _zone(i: int) -> str:
    if i < 13:
        return "Zone-1 Ahmedabad West"
    if i < 25:
        return "Zone-2 Ahmedabad Central"
    if i < 37:
        return "Zone-3 SG Highway"
    if i < 43:
        return "Zone-4 Gandhinagar Highway"
    return "Zone-5 Gandhinagar"


def _install_date(i: int) -> _dt.date:
    # deterministic spread 2017..2024 so gap-analysis surfaces ageing infrastructure
    return _dt.date(2017 + (i % 8), 1 + (i * 3) % 12, 15)


def _firmware(i: int) -> str:
    major = 2 + (i % 3)  # v2/v3/v4 — v2.x is end-of-life / ageing
    return f"v{major}.{(i * 3) % 10}"


def _health(i: int, offline: bool) -> str:
    if offline:
        return "offline"
    if i % 11 == 0:
        return "degraded"
    return "healthy"


def _maintenance(i: int) -> str:
    if i % 17 == 0:
        return "in_repair"
    if i % 9 == 0:
        return "scheduled"
    return "ok"


CAMERAS = [
    {
        "id": f"CAM-{i + 1:03d}",
        "name": _NAMES[i],
        "lat": la,
        "lon": lo,
        "vendor": _VENDORS[i % len(_VENDORS)],
        "vms": _VMS[i % len(_VMS)],
        "protocol": _PROTOCOLS[i % len(_PROTOCOLS)],
        "status": "offline" if i in OFFLINE_INDICES else "online",
        "department": _DEPARTMENTS[i % len(_DEPARTMENTS)],
        "zone": _zone(i),
        "stream_url": f"rtph://{_PROTOCOLS[i % 4]}-gw{i % 6}.local:554/live/cam{i + 1:03d}".replace("rtph", "rtsp"),
        "direction": "North-bound" if i % 2 == 0 else "South-bound",
        "install_date": _install_date(i),
        "health": _health(i, i in OFFLINE_INDICES),
        "maintenance_status": _maintenance(i),
        "coverage_radius_m": 60 + (i * 13) % 90,
        "firmware": _firmware(i),
    }
    for i, (la, lo) in enumerate(_COORDS)
]

WATCHLIST = [
    {
        "category": "stolen_vehicle",
        "plate": "GJ-01-KA-1234",
        "description": "Stolen from Vastrapur — FIR 1246/2026, Vastrapur PS",
        "color": "Black",
        "model": "Hyundai Creta",
        "notes": "Designated tracking target for field validation test case",
    },
    {
        "category": "blacklisted_vehicle",
        "plate": "GJ-05-AB-4321",
        "description": "Repeat traffic offender — 47 pending e-challans",
        "color": "White",
        "model": "Maruti Swift",
        "notes": "",
    },
    {
        "category": "stolen_vehicle",
        "plate": "GJ-01-R-5555",
        "description": "Stolen two-wheeler — Sabarmati PS FIR 889/2026",
        "color": "Red",
        "model": "Honda Activa",
        "notes": "",
    },
    {
        "category": "blacklisted_vehicle",
        "plate": "GJ-18-MX-0099",
        "description": "Blacklisted cab — transport permit revoked",
        "color": "Silver",
        "model": "Toyota Etios",
        "notes": "",
    },
    {
        "category": "wanted_person",
        "person_name": "Rahil Shaikh",
        "description": "Wanted in cheating case — Shahibaug PS; last seen near Kalupur",
        "notes": "Face-embedding match module scheduled in roadmap phase 2",
    },
]

DESIGNATED_PLATE = "GJ-01-KA-1234"
ROUTE_STOP_INDICES = [1, 3, 7, 10, 14, 17, 20, 24, 27, 31, 34, 37, 40, 43, 46, 49]
ROUTE_STEP_SECONDS = [96, 104, 88, 112, 97, 90, 108, 101, 86, 110, 95, 99, 87, 105, 93]
