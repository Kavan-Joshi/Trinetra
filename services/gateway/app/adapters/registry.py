"""Adapter registry — the modular, vendor-neutral adapter framework
(Architecture Principles: modular adapter-based frameworks; cameras/VMS
replaceable without redesign).

Each live protocol adapter registers itself here by protocol name. The gateway
builds adapters for the configured protocol groups via :func:`build`, so adding
a new vendor/protocol is "register a new adapter" — not "edit the gateway
main loop". Adapters conform to :class:`BaseAdapter` (``__init__(name, cameras,
js)`` + ``async run()``).

Example — adding a hypothetical ONVIF-T profile adapter::

    # in a new module imported by main.py
    from .base import BaseAdapter
    from .registry import registry

    class ONVIFTAdapter(BaseAdapter):
        async def run(self): ...

    registry.register("onvif-t", ONVIFTAdapter)
"""

from __future__ import annotations

import logging
from typing import Callable

from .base import BaseAdapter

log = logging.getLogger("trinetra.adapters")

AdapterFactory = Callable[[str, list, object], BaseAdapter]


class AdapterRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, AdapterFactory] = {}

    def register(self, protocol: str, factory: AdapterFactory) -> None:
        self._factories[protocol] = factory

    def protocols(self) -> list[str]:
        return list(self._factories)

    def create(self, protocol: str, cameras, js) -> BaseAdapter | None:
        factory = self._factories.get(protocol)
        if factory is None:
            return None
        return factory(protocol, cameras, js)


registry = AdapterRegistry()
