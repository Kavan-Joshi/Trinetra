"""Pluggable analytics-engine interface (Architecture Principles: AI modules are
replaceable without redesign).

The gateway runs one :class:`AnalyticsEngine` per live adapter to detect/classify
objects and read plates from decoded frames. Concrete implementations drop in
behind this interface — the default is YOLOv8n + RapidOCR
(:mod:`services.gateway.app.pipeline`); a future face/Re-ID engine, a vendor-SDK
engine, or a cloud inference engine can be added by implementing this ABC and
selecting it via ``TRINETRA_ANALYTICS_ENGINE``. Neither the adapter code, the
event-bus schema, nor the correlator need to change.

A detection dict returned by :meth:`process` has the shape::

    {
        "bbox": [x1, y1, x2, y2],
        "vehicle_class": "car" | "motorcycle" | "bus" | "truck" | ...,
        "plate": str | None,
        "plate_confidence": float | None,
        "color": str | None,
        "ts": datetime,
        "save_snapshot": callable[[str], None],
    }
"""

from __future__ import annotations

import abc
from typing import Any


class AnalyticsEngine(abc.ABC):
    """Abstract analytics engine. Implementations must be stateless across calls
    apart from lazy model loading (``process`` may be called from a thread)."""

    @abc.abstractmethod
    def process(self, frame_bgr: Any, camera: Any) -> list[dict]:
        """Analyse a single BGR frame and return a list of detection dicts."""
        ...
