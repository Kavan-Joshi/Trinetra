import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from sim.data import DESIGNATED_PLATE, OFFLINE_INDICES, ROUTE_STOP_INDICES
from sim.scenario import build_scenario


def test_scenario_builds_without_error():
    passes = build_scenario()
    assert len(passes) > 100


def test_designated_route_hits_every_stop_in_order():
    passes = build_scenario()
    route = [p for p in passes if p.plate == DESIGNATED_PLATE]
    assert len(route) == len(ROUTE_STOP_INDICES)
    assert [p.camera_id for p in route] == [f"CAM-{i + 1:03d}" for i in ROUTE_STOP_INDICES]
    offsets = [p.offset_s for p in route]
    assert offsets == sorted(offsets)
    assert all(p.plate_confidence and p.plate_confidence >= 0.85 for p in route)


def test_scenario_never_uses_offline_cameras():
    passes = build_scenario()
    offline = {f"CAM-{i + 1:03d}" for i in OFFLINE_INDICES}
    assert all(p.camera_id not in offline for p in passes)


def test_all_passes_have_valid_field_types():
    for p in build_scenario():
        assert p.kind in {"vehicle", "person", "object"}
        assert isinstance(p.direction, str) and p.direction
        assert 20 <= p.speed_kmh <= 120
        assert p.vehicle_class in {"car", "motorcycle", "truck", "bus"}
        if p.plate:
            assert 0.5 <= p.plate_confidence <= 1.0


def test_background_and_watchlist_hits_present():
    passes = build_scenario()
    assert any(p.plate == "GJ-05-AB-4321" for p in passes)
    assert any(p.plate == "GJ-01-R-5555" for p in passes)
    assert any(p.attributes.get("anomaly") for p in passes)
    assert any(p.kind == "person" for p in passes)
    assert any(p.kind == "object" for p in passes)
