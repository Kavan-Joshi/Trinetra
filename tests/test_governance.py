import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from sim.data import COMMUNITY_CAMERAS, DEPARTMENTS
from sim.records import CCTNS_FEED, NAFIS_MATCHES, VAHAN_RECORDS
from trinetra_core.plates import normalize_plate


def test_departments_seeded_with_retention():
    assert len(DEPARTMENTS) == 28  # 26 statewide + GSRTC + Panchayat (hackathon dataset)
    codes = [d["code"] for d in DEPARTMENTS]
    assert len(set(codes)) == 28
    for d in DEPARTMENTS:
        assert d["name"] and d["code"]
        assert d["retention_events_days"] in (7, 15, 30)
        assert d["retention_evidence_days"] >= 30


def test_community_cameras_have_consent():
    assert len(COMMUNITY_CAMERAS) >= 2
    for c in COMMUNITY_CAMERAS:
        assert c["source_type"] == "community"
        assert c["consent"] is True
        assert c["stream_url"].startswith("rtsp://")


def test_cctns_feed_is_sourced_and_referenced():
    assert len(CCTNS_FEED) >= 3
    for entry in CCTNS_FEED:
        assert entry["source_system"] == "cctns"
        assert entry["source_ref"]
        assert entry["category"] in {
            "stolen_vehicle", "blacklisted_vehicle", "wanted_person", "missing_person", "suspect",
        }


def test_vahan_keys_are_normalized_plates():
    for plate_norm, rec in VAHAN_RECORDS.items():
        assert plate_norm == normalize_plate(plate_norm)
        assert rec["owner_name"]
        assert rec["model"]
        assert "source_ref" in rec


def test_nafis_matches_carry_scores():
    assert len(NAFIS_MATCHES) >= 1
    for m in NAFIS_MATCHES:
        assert m["source_system"] == "nafis"
        assert 0.0 <= m["score"] <= 1.0
        assert m["fir_ref"]
