import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinetra_core.records import mock_enricher


def run(coro):
    return asyncio.run(coro)


def test_plate_dossier_returns_vahan_and_cctns():
    e = mock_enricher()
    dossier = run(e.lookup_plate("GJ-18-X-3001"))
    assert dossier["vahan"]["owner_name"] == "Surat Transport Pvt Ltd"
    assert dossier["vahan"]["model"] == "LPT 1613"
    assert dossier["cctns"]["category"] == "stolen_vehicle"
    assert dossier["cctns"]["source_system"] == "cctns"


def test_plate_enrichment_includes_sarathi_for_owner():
    e = mock_enricher()
    out = run(e.enrich_plate("GJ11S4826"))
    assert out["vahan"]["owner_name"] == "Bharat P. Solanki"
    assert out["sarathi"]["dl_number"]
    assert out["sarathi"]["valid"] is False


def test_unknown_plate_returns_empty_dossier():
    e = mock_enricher()
    dossier = run(e.lookup_plate("ZZ99ZZ9999"))
    assert dossier["vahan"] is None
    assert dossier["cctns"] is None


def test_person_dossier_returns_cctns_and_nafis():
    e = mock_enricher()
    out = run(e.enrich_person("Wanted Suspect A"))
    assert out["cctns"]["category"] == "wanted_person"
    assert out["nafis"]["matched"] is True
    assert out["nafis"]["score"] >= 0.8


def test_unknown_person_returns_no_match():
    e = mock_enricher()
    out = run(e.enrich_person("Nobody"))
    assert out["cctns"] is None
    assert out["nafis"]["matched"] is False


def test_cctns_feed_has_sourced_entries():
    e = mock_enricher()
    feed = run(e.cctns_feed())
    assert len(feed) >= 3
    assert all(item["source_system"] == "cctns" for item in feed)
