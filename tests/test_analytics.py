import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from trinetra_core.analytics import AnalyticsEngine


def test_analytics_engine_is_abstract():
    with pytest.raises(TypeError):
        AnalyticsEngine()


def test_analytics_engine_subclass_contract():
    class DummyEngine(AnalyticsEngine):
        def process(self, frame_bgr, camera):
            return [{"bbox": [0, 0, 1, 1], "plate": "GJ01KA1234", "plate_confidence": 0.9,
                     "vehicle_class": "car", "color": None, "ts": None, "save_snapshot": lambda p: None}]

    e = DummyEngine()
    dets = e.process(None, None)
    assert len(dets) == 1
    assert dets[0]["plate"] == "GJ01KA1234"
