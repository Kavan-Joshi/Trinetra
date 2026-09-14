import logging

from .rtsp import RTSPAdapter

log = logging.getLogger("trinetra.adapter.onvif")

_ONVIF_NOTE = (
    "ONVIF federation: resolve camera via GetProfiles/GetStreamUri (SOAP), then hand the RTSP "
    "media URI to the standard RTSP ingestion path. Full SOAP client lands with the vendor-SDK "
    "integration phase; this adapter already normalizes ONVIF cameras into the same event stream."
)


class ONVIFAdapter(RTSPAdapter):
    async def run(self) -> None:
        log.info(_ONVIF_NOTE)
        await super().run()
