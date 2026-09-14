import logging

from trinetra_core.bus import SUBJECT_EVENTS, publish_json
from trinetra_core.models import Camera, DetectionEvent

log = logging.getLogger("trinetra.adapter")


class BaseAdapter:
    def __init__(self, name: str, cameras: list[Camera], js):
        self.name = name
        self.cameras = cameras
        self.js = js
        self._emitted = 0

    async def emit(self, event: DetectionEvent) -> None:
        await publish_json(self.js, SUBJECT_EVENTS, event)
        self._emitted += 1
        if self._emitted % 50 == 0:
            log.info("adapter[%s] emitted %d events", self.name, self._emitted)

    async def run(self) -> None:
        raise NotImplementedError
