import random
from dataclasses import dataclass, field

from .data import OFFLINE_INDICES, ROUTE_STEP_SECONDS, ROUTE_STOP_INDICES, DESIGNATED_PLATE


@dataclass
class PassSpec:
    camera_id: str
    offset_s: float
    plate: str | None = None
    kind: str = "vehicle"
    vehicle_class: str = "car"
    color: str = "Grey"
    direction: str = "North-bound"
    speed_kmh: float = 50.0
    plate_confidence: float | None = None
    attributes: dict = field(default_factory=dict)


def build_scenario() -> list[PassSpec]:
    rng = random.Random(2026)
    passes: list[PassSpec] = []

    offset = 30.0
    for i, idx in enumerate(ROUTE_STOP_INDICES):
        passes.append(PassSpec(
            camera_id=f"CAM-{idx + 1:03d}",
            offset_s=offset,
            plate=DESIGNATED_PLATE,
            vehicle_class="car",
            color="Black",
            direction="North-bound",
            speed_kmh=48 + (i * 7) % 25,
            plate_confidence=round(0.88 + (i % 10) * 0.009, 3),
            attributes={"tracked_target": True},
        ))
        offset += ROUTE_STEP_SECONDS[i] if i < len(ROUTE_STEP_SECONDS) else 100

    passes.append(PassSpec("CAM-016", 420, plate="GJ-05-AB-4321", vehicle_class="car", color="White", direction="East-bound", speed_kmh=38, plate_confidence=0.93))
    passes.append(PassSpec("CAM-034", 1180, plate="GJ-05-AB-4321", vehicle_class="car", color="White", direction="West-bound", speed_kmh=42, plate_confidence=0.91))
    passes.append(PassSpec("CAM-027", 860, plate="GJ-01-R-5555", vehicle_class="motorcycle", color="Red", direction="North-bound", speed_kmh=35, plate_confidence=0.87))

    passes.append(PassSpec("CAM-013", 700, kind="person", attributes={
        "anomaly": True, "anomaly_type": "crowd_anomaly", "anomaly_confidence": 0.86,
        "anomaly_detail": "Sudden crowd formation near Delhi Darwaja junction",
    }))
    passes.append(PassSpec("CAM-046", 1250, kind="object", attributes={
        "anomaly": True, "anomaly_type": "unattended_object", "anomaly_confidence": 0.81,
        "anomaly_detail": "Unattended bag detected at Sector 7 bus stop",
    }))

    districts = ["GJ-01", "GJ-05", "GJ-18", "GJ-27"]
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    classes = [
        ("car", ["White", "Grey", "Black", "Silver", "Blue", "Red"]),
        ("motorcycle", ["Red", "Black", "Blue"]),
        ("truck", ["White", "Orange"]),
        ("bus", ["Yellow"]),
    ]
    online = [i for i in range(50) if i not in OFFLINE_INDICES]
    for _ in range(55):
        plate = f"{rng.choice(districts)}-{rng.choice(letters)}{rng.choice(letters)}-{rng.randint(1000, 9999)}"
        vehicle_class, colors = rng.choice(classes)
        for _ in range(rng.randint(2, 5)):
            idx = rng.choice(online)
            passes.append(PassSpec(
                camera_id=f"CAM-{idx + 1:03d}",
                offset_s=round(rng.uniform(10, 2350), 1),
                plate=plate,
                vehicle_class=vehicle_class,
                color=rng.choice(colors),
                direction=rng.choice(["North-bound", "South-bound", "East-bound", "West-bound"]),
                speed_kmh=round(rng.uniform(25, 80), 1),
                plate_confidence=round(rng.uniform(0.70, 0.96), 3),
            ))
    return sorted(passes, key=lambda p: p.offset_s)
