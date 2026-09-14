# Trinetra — Architecture Principles Compliance

How the Trinetra platform satisfies the RFP's architecture principles. Trinetra uses the **hybrid approach** (reference Models 1 + 3 + 2 — see [`HLD.md`](HLD.md) §0): a canonical registry/GIS foundation (Model 1), federation middleware through edge gateway adapters (Model 3), and unified analytics/alerting at the center (Model 2).

## Principle → Implementation map

| RFP principle | How Trinetra delivers it | Extension point |
|---|---|---|
| **Open** | 100% open-source stack: FastAPI, React, PostgreSQL+PostGIS, Redis, NATS JetStream, YOLOv8 (Ultralytics, AGPL/Apache), RapidOCR, ffmpeg, Leaflet. No proprietary runtime dependency. | — |
| **Modular** | Independently deployable services: `gateway`, `correlator`, `core_api`, `records`, `notifier`, `streamer`, `janitor`. Each has its own Dockerfile + requirements and communicates only via the NATS event bus or HTTP APIs. | Add a service without touching others |
| **Scalable** | Gateways scale horizontally (one per site); correlator/core-api scale via JetStream queue groups; Postgres shards by zone. See [`SCALABILITY.md`](SCALABILITY.md). Bandwidth: ~1–2 Gbps event plane for 80k cameras vs 320 Gbps raw. | — |
| **Secure** | JWT + department-scoped RBAC, immutable audit trail, TLS, mTLS for records connectors, PII/chain-of-custody. See [`SECURITY.md`](SECURITY.md). | — |
| **Standards-based** | OpenAPI (core API at `/docs`), AsyncAPI (event bus — [`asyncapi.yaml`](asyncapi.yaml)), ONVIF, **GB/T 28181**, RTSP, HTTP-MJPEG, PostGIS, JWT (RFC 7519). | — |
| **Vendor-neutral** | No vendor-specific core. Every camera enters through the canonical registry with vendor/VMS/protocol metadata; the normalized `DetectionEvent` schema is the only thing on the bus. 8 vendors / 6 VMS / 5 protocols in the pilot. | — |
| **Avoid vendor lock-in** | Cameras, VMS, analytics, and storage are all behind interfaces (see below). Replacing any one does not require redesigning the others. | — |
| **Technology-agnostic / heterogeneous multi-vendor** | The registry absorbs heterogeneity; adapters normalise vendor formats into one event schema; AI engines are pluggable; storage is pluggable. | — |
| **Future enhancements without significant redesign** | New camera vendor = new adapter; new analytics = new engine; new department = registry row; new alert channel = notifier rule. None touch the core bus/correlator/schema. | — |

## Modular adapter-based framework (cameras & VMS)

**Seam:** `services/gateway/app/adapters/` — `BaseAdapter` + `AdapterRegistry`.

Every live protocol adapter extends `BaseAdapter` (`__init__(name, cameras, js)` + `async run()`) and **self-registers** with the `AdapterRegistry` by protocol name. The gateway builds adapters for the configured protocol groups via `registry.create(proto, …)` — it never hardcodes `if protocol == …`. Adding a new vendor/protocol is "write an adapter module that registers itself", not "edit the gateway main loop".

Registered today:
- `rtsp` → `RTSPAdapter` (universal fallback; forces TCP, backoff reconnect, PTS timing)
- `onvif` → `RTSPAdapter` (ONVIF `GetStreamUri` resolves to RTSP, reuses the RTSP path)
- `gb28181` → `GB28181Adapter` (GB/T 28181 SIP signaling → RTSP media)
- `http-mjpeg`, `vendor-api` → plugin surface for VMS-SDK bridges (Milestone/Genetec/CP-Plus) — documented seam

**Add a vendor-SDK VMS bridge** (e.g., a Milestone XProtect connector):
```python
# services/gateway/app/adapters/milestone.py
from .base import BaseAdapter
from .registry import registry
class MilestoneAdapter(BaseAdapter):
    async def run(self): ...          # subscribe to the VMS event stream
registry.register("vendor-api", MilestoneAdapter)
```
Then import the module in `main.py` — no other change.

## AI modules replaceable (analytics engines)

**Seam:** `packages/trinetra_core/analytics.py` — `AnalyticsEngine` ABC.

The gateway runs one `AnalyticsEngine` per live adapter. The default is `AnalyticsPipeline` (YOLOv8n + RapidOCR ANPR). Engines are selected by the `get_analytics_engine()` factory from `TRINETRA_ANALYTICS_ENGINE` (default `yolo_rapidocr`; `mock` for CPU-less tests). A `MockAnalyticsEngine` is provided. Neither the adapter, the event-bus schema, nor the correlator change when the engine changes.

**Swap to a future face/Re-ID or vendor-SDK engine:**
```python
# implement the ABC
class FaceReIDEngine(AnalyticsEngine):
    def process(self, frame, camera): ...   # return detection dicts
# register in the factory (or via entry-point) and set TRINETRA_ANALYTICS_ENGINE=face_reid
```
The downstream correlator → records → notifier → console pipeline is unchanged.

## Storage platforms replaceable

Evidence (snapshot frames) is written to a configurable `TRINETRA_EVIDENCE_DIR` (volume) and served via the core API. The volume maps to local disk in the pilot and to S3-compatible object storage in production (lifecycle-tiered — see [`SCALABILITY.md`](SCALABILITY.md) §4). Event metadata lives in PostgreSQL/PostGIS (shardable by zone). No application code changes between local and object storage — only the mount/config.

## Documented standard APIs, open protocols, SDKs

- **OpenAPI**: core REST API auto-documented at `http://localhost:8000/docs` (registry, watchlist, events, alerts, records, gap-analysis, departments, notifications, community).
- **AsyncAPI**: the NATS event-bus contract — [`docs/asyncapi.yaml`](asyncapi.yaml) — subjects `trinetra.events.raw`, `trinetra.alerts.new`, `trinetra.watchlist.changed` with the `DetectionEvent` / `AlertPayload` schemas.
- **Open protocols**: RTSP, ONVIF, GB/T 28181, HTTP-MJPEG.
- **SDKs / plugin surfaces**: `BaseAdapter` (cameras/VMS), `AnalyticsEngine` (AI), `RecordsConnector` family (government DBs — VAHAN/SARTHI/CCTNS/NAFIS), `EvidenceStore` (storage), notifier dispatch functions (alert channels). Each is a small ABC behind which concrete implementations drop in.

## Government-database interoperability

**Seam:** `packages/trinetra_core/records.py` — `VahanConnector`, `SarathiConnector`, `CctnsConnector`, `NafisConnector` ABCs + `RecordsEnricher` facade. Mock connectors run the demo; real CCTNS/VAHAN/NAFIS connectors drop in behind the same interface (mTLS, service accounts) with no correlator change. See [`INTEGRATION.md`](INTEGRATION.md) §2.

## Permitted approach

**Hybrid (Models 1 + 3 + 2)**, justified in [`HLD.md`](HLD.md) §0: Model 1 registry/GIS foundation + Model 3 VMS-federation middleware (edge gateways) + Model 2 unified viewing/analytics at the center, unified by "detect at the edge, correlate at the center."
