import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from trinetra_core.trajectory import same_session


T0 = datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc)


def test_points_within_gap_share_session():
    assert same_session(T0, T0 + timedelta(minutes=30)) is True
    assert same_session(T0, T0 + timedelta(seconds=3600)) is True


def test_points_beyond_gap_start_new_session():
    assert same_session(T0, T0 + timedelta(seconds=3601)) is False
    assert same_session(T0, T0 + timedelta(hours=6)) is False


def test_custom_gap():
    assert same_session(T0, T0 + timedelta(minutes=10), gap_seconds=600) is True
    assert same_session(T0, T0 + timedelta(minutes=11), gap_seconds=600) is False


def test_out_of_order_timestamps_do_not_match():
    assert same_session(T0, T0 - timedelta(minutes=1)) is False
