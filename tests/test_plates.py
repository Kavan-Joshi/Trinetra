import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from trinetra_core.plates import format_plate, normalize_plate, plate_match


def test_normalize_strips_punctuation_and_case():
    assert normalize_plate("gj-01-ka-1234") == "GJ01KA1234"
    assert normalize_plate(" GJ 01 KA 1234 ") == "GJ01KA1234"
    assert normalize_plate(None) == ""
    assert normalize_plate("") == ""


def test_format_indian_plate():
    assert format_plate("GJ01KA1234") == "GJ-01-KA-1234"
    assert format_plate("GJ05AB4321") == "GJ-05-AB-4321"
    assert format_plate("XX999") == "XX999"


def test_plate_match_is_normalization_insensitive():
    assert plate_match("gj 01 ka 1234", "GJ-01-KA-1234") is True
    assert plate_match("GJ01KA1235", "GJ-01-KA-1234") is False
    assert plate_match(None, "GJ-01-KA-1234") is False
