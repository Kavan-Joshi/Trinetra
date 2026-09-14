# Trinetra — Integration Architecture

How the platform integrates with heterogeneous cameras, incumbent VMS, government databases, private/community cameras, and external law-enforcement systems. This complements the HLD; the headline design rule throughout is **standardised contracts, federation at the edge, events (not video) at the center**.

## 1. Camera & VMS federation (heterogeneous infrastructure)

Every camera is a first-class record in the canonical registry: ID, lat/long, vendor, VMS, **protocol**, stream URI, status, **department**, zone, source-type. Analytics and GIS never talk to a camera directly — only to its registry entry. This is what absorbs vendor/VMS/protocol heterogeneity (RFP Challenge 01).

**Supported protocols** (one adapter worker per protocol group in the gateway):

| Protocol | Adapter | Notes |
|---|---|---|
| `rtsp` | `RTSPAdapter` | Universal fallback; virtually every Indian CCTV estate exposes it. |
| `onvif` | `ONVIFAdapter` → RTSP | `GetProfiles`/`GetStreamUri` resolves to an RTSP URI; reuses the RTSP path. |
| `http-mjpeg` | vendor-SDK plugin surface | Demonstrates the plugin seam for simple IP cameras. |
| `vendor-api` | VMS bridge (Milestone/Genetec/CP-Plus SDK) | Incumbent VMS event streams are bridged so departments keep existing analytics. |
| `gb28181` | `GB28181Adapter` | **GB/T 28181** — the Chinese national standard (SIP signaling + RTP/RTSP media), dominant for the Hikvision/Dahua/CP-Plus estate prevalent in India. Models REGISTER/catalog/INVITE; media resolves to RTSP. |

A normalised `DetectionEvent` schema is the single contract on the bus regardless of source — downstream systems never see vendor formats. Raw video stays at the site; the WAN carries events + compressed evidence frames only.

## 1.5 Model 1 — Registry & GIS foundation (the mandatory baseline)

Model 1 is the foundational layer (no live streaming/recording) that the other models build on. It is fully delivered:

- **Centralised registry** — every camera is a first-class record with location, department, vendor, VMS, protocol, ownership, connectivity status, **install date, health, maintenance status, coverage radius, firmware**, source-type (gov/community) + consent. Onboarding via **manual entry** (`POST /api/v1/cameras`), **bulk JSON** (`POST /api/v1/cameras/bulk`), **bulk CSV upload** (`POST /api/v1/cameras/import`), and **API**.
- **Interactive GIS map** (Leaflet + PostGIS) with department, camera-type, status and **health** layers, plus a **coverage-footprint toggle** (per-camera coverage circles coloured by health).
- **Health & maintenance monitoring** — `GET /api/v1/cameras/health` summary; filter the registry by health/maintenance; per-camera health badges.
- **Gap-analysis reports** — `GET /api/v1/gap-analysis/coverage` (per-zone coverage + gap flags), `/ageing` (age buckets, EOL firmware, maintenance), `/report` (combined), `/report/download` (CSV). Sample report: [`SAMPLE_GAP_ANALYSIS_REPORT.md`](SAMPLE_GAP_ANALYSIS_REPORT.md).
- **Role-based search, filtering, export** — department-scoped RBAC; `GET /api/v1/cameras/export` (CSV); metadata **audit trail** for every onboarding/change.

## 2. Government records integration (VAHAN / SARTHI / eGujCop-CCTNS / AFIS / NAFIS)

This is the RFP's headline integration requirement: *"integrated with these databases to enable automated real-time alerts and proactive monitoring."* Trinetra federates records the same way it federates feeds — through connectors behind a small interface (`packages/trinetra_core/records.py`).

**Two integration modes:**

- **Inbound (auto-watchlist):** the `records` service consumes the CCTNS/eGujCop feed of stolen/wanted/missing/blacklisted records and upserts them into the watchlist, tagged with `source_system` (cctns) and `source_ref` (FIR/record id). The manual watchlist becomes a **live, database-backed watchlist**. On upsert it publishes `trinetra.watchlist.changed` so every correlator instance refreshes its Redis cache.
- **Outbound (real-time enrichment):** on a plate hit, the correlator calls the records enricher to attach **VAHAN** vehicle/owner details and **SARTHI** DL status to the alert; for persons, **CCTNS** person records + **NAFIS** fingerprint/face match scores. The alert carries `source_system`, `source_ref`, and an `enrichment` block visible to operators.

**Connector abstraction (real connectors drop in behind the same ABCs):**

```
VahanConnector   .lookup_plate(plate_norm) -> VehicleRecord
SarathiConnector .lookup_owner(owner_name) -> DL record
CctnsConnector   .watchlist_updates() -> [records]; .lookup_person(name); .lookup_plate_history(plate)
NafisConnector   .search_fingerprint(name) -> FingerprintMatch
RecordsEnricher  .enrich_plate(plate) / .enrich_person(name) / .lookup_plate(plate) / .cctns_feed()
```

The demo ships **mock connectors** backed by `sim/records.py` (scripted CCTNS feed, VAHAN table, SARTHI DLs, NAFIS matches) so the full alert/enrichment flow runs on a laptop with no real DB access. Production swaps in real connectors: CCTNS API gateway (NCRB), NIDC VAHAN, NCRB NAFIS — mTLS + service accounts, Redis cache + circuit breaker, every lookup audited (chain of custody), PII per DPDP Act 2023 / GPDPL.

**Operator-facing surface:** the `Records` page exposes a plate dossier (VAHAN + CCTNS hit + SARTHI) and a person dossier (CCTNS + NAFIS); watchlist rows and alert cards show the source system + FIR reference.

## 3. Community / private camera viewing

The RFP requires viewing capability for "public-facing CCTV cameras installed by societies, malls, commercial establishments." Trinetra supports this via:

- **Self-service onboarding** (`POST /api/v1/community/cameras`) — a nodal officer/owner registers a camera with explicit consent; it enters the registry as `source_type=community`, `consent=true`, with a restricted scope.
- **Live viewing** via the `streamer` service (see §4).

## 4. Live viewing transport

The `streamer` service serves per-camera live video to the operator console:

- **HLS (default, ~3–10 s latency):** an ffmpeg process per camera generates an HLS playlist on demand. In simulation mode it reads a `testsrc` pattern with the camera name + clock overlaid; in live mode it reads the camera's RTSP URL. Only one ffmpeg per camera runs, and only while an operator is watching (idle processes reaped after 30 s) — a stream is pulled only on demand, consistent with "move events, not video."
- **WebRTC (opt-in, sub-second):** a WHIP endpoint (`POST /whip/{cam}`) backed by aiortc publishes a generated video track. Enable at build time with `INSTALL_WEBRTC=true`; if absent, the console falls back to HLS.

Routing: the browser requests `GET /api/v1/cameras/{id}/stream` → signed, short-lived HLS + WebRTC URLs; nginx proxies `/stream/` to the streamer. The `Live View` page offers a transport toggle.

## 5. Alert fan-out to field units

The `notifier` service subscribes to `trinetra.alerts.new` and routes each alert by category to channels (SMS / email / webhook-to-CCTNS / FCM mobile push) per a routing table. Every dispatch is recorded as a `NotificationRow` and shown in the `Fan-out` panel. SMS/email/FCM are mock-dispatched (logged) for the demo; the webhook channel performs a real HTTP POST to the configured endpoint so end-to-end fan-out is observable. Real gateways (MSG91/BSNL SMS, FCM, CCTNS webhook) drop in behind the `dispatch()` functions.

## 6. Formal contracts

- **OpenAPI:** the core API spec is auto-generated at `/docs` (FastAPI).
- **AsyncAPI:** the NATS event-bus contract is published in [`docs/asyncapi.yaml`](asyncapi.yaml) — subjects `trinetra.events.raw`, `trinetra.alerts.new`, `trinetra.watchlist.changed` with the `DetectionEvent` / `AlertPayload` / `WatchlistChanged` message schemas.
- **Normalised event/alert schemas:** defined in `packages/trinetra_core/models.py`; the bus carries only these, never vendor formats.
