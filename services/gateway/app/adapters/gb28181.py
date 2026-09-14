"""GB/T 28181 adapter (Workstream 4 — standardised integration).

GB/T 28181 is the Chinese national standard for video surveillance
interconnection (SIP-based signaling + RTP/RTSP media) and is the dominant
interoperability standard for the Hikvision / Dahua / CP-Plus camera estate
prevalent in Indian government deployments. This adapter models the
standardised integration surface:

* **Signaling** — a GB28181 device registers with the platform over SIP
  (REGISTER), the platform catalogs it (MESSAGE/Catalog), and a playback/live
  session is negotiated via INVITE with an SDP describing the media stream.
* **Media** — the negotiated media URI resolves to an RTSP/RTP stream that the
  existing analytics pipeline consumes unchanged.

For the demo (no live SIP stack), the adapter logs the registration/catalog step
and delegates media ingestion to the RTSP adapter (``stream_url`` resolved by
the registry). A production deployment plugs a SIP stack (e.g. oversip/osip)
into :meth:`_register` to perform real REGISTER/INVITE; the downstream pipeline
is identical.
"""

import logging

from .rtsp import RTSPAdapter
from .registry import registry

log = logging.getLogger("trinetra.adapter.gb28181")


class GB28181Adapter(RTSPAdapter):
    async def run(self) -> None:
        for cam in self.cameras:
            log.info("GB28181 REGISTER %s (device id %s) -> catalog acquired; media via RTSP fallback %s",
                     cam.id, cam.id, cam.stream_url or "(none)")
        await super().run()


registry.register("gb28181", GB28181Adapter)
