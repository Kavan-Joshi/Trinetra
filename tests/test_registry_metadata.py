import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from sim.data import CAMERAS, COMMUNITY_CAMERAS


def test_cameras_carry_model1_metadata():
    for c in CAMERAS:
        assert c["install_date"] is not None
        assert c["health"] in {"healthy", "degraded", "offline"}
        assert c["maintenance_status"] in {"ok", "scheduled", "in_repair"}
        assert 30 <= c["coverage_radius_m"] <= 200
        assert c["firmware"].startswith("v")


def test_ageing_and_degraded_variety_present():
    today = date.today()
    ageing = [c for c in CAMERAS if (today - c["install_date"]).days / 365.25 >= 5]
    degraded = [c for c in CAMERAS if c["health"] != "healthy"]
    in_repair = [c for c in CAMERAS if c["maintenance_status"] != "ok"]
    assert len(ageing) >= 1, "expected some ageing cameras for gap-analysis"
    assert len(degraded) >= 1, "expected some degraded-health cameras"
    assert len(in_repair) >= 1, "expected some cameras under maintenance"


def test_eol_firmware_variety_present():
    eol = [c for c in CAMERAS if c["firmware"].startswith("v2")]
    assert len(eol) >= 1, "expected some end-of-life v2.x firmware cameras"


def test_offline_cameras_marked_offline_health():
    from sim.data import OFFLINE_INDICES
    for i, c in enumerate(CAMERAS):
        if i in OFFLINE_INDICES:
            assert c["status"] == "offline"
            assert c["health"] == "offline"


def test_community_cameras_use_default_metadata():
    for c in COMMUNITY_CAMERAS:
        assert c["source_type"] == "community"
        assert c["consent"] is True
