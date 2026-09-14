# Trinetra — High-Level Design (HLD)
### Integrated Video Management & Analytics Platform · Gujarat Police Innovation Challenge 2026

---

## 0. Integration Model Decision (mandatory per problem statement)

**Chosen: Justified Hybrid — Model 1 (Registry & GIS foundation) + Model 3 (VMS federation middleware) + Model 2 (Unified viewing & analytics), unified by the design principle "Detect at the Edge, Correlate at the Center."**

**Why this hybrid, in 4 sentences:**

1. A statewide estate of ~80,000 already-deployed cameras across incumbent VMS platforms cannot be replaced by a central VMS (Model 4) — no state rips out working surveillance mid-operation, and raw centralization demands ~320 Gbps of permanent video transit which is physically and economically infeasible.
2. Pure middleware (Model 3) demonstrates plumbing but delivers none of the AI value the problem statement demands; pure unified viewing (Model 2) centralizes inference on streams the network cannot carry.
3. Trinetra therefore federates *feeds* through gateway adapters at each site (Model 3), runs detection and ANPR **locally at the gateway** so only structured events + evidence frames (~1 KB + ~100 KB, not 4 Mbps) cross the WAN, and centralizes what actually needs to be central: watchlist matching, cross-camera trajectory correlation, alerting, GIS, and search (Model 2).
4. Everything is grounded in a canonical camera/asset registry with GIS coordinates and per-camera VMS/vendor/protocol metadata (Model 1, the mandatory baseline), which is what makes 50 heterogeneous pilot cameras and 80,000 statewide cameras behave as one system.

**The one-line thesis the judges should remember:** *other proposals move video; Trinetra moves events.* Scaling to 80,000 cameras means scaling O(events), not O(video).

---

## 1. Overall Architecture

### 1.1 Component diagram

```
                             ┌──────────────────────────────────────────────────────────┐
                             │                     STATE DATA CENTRE                     │
   ┌──────────────┐  events  │  ┌────────────┐   ┌──────────────┐   ┌────────────────┐   │
   │ SITE A       │ ───────▶ │  │   NATS     │──▶│  CORRELATOR  │──▶│ PostgreSQL 16  │   │
   │ Hikvision ×  │  + snap- │  │ JetStream  │   │  watchlist   │   │  + PostGIS     │   │
   │ Milestone    │  shots   │  │ (event bus)│   │  matching    │   │  registry/     │   │
   │ ┌──────────┐ │          │  └─────┬──────┘   │  trajectory  │   │  events/alerts/│   │
   │ │ GATEWAY  │ │          │        │          │  alerting    │   │  tracks/audit  │   │
   │ │ adapters │ │          │        ▼          │  face match  │   └────────────────┘   │
   │ │ RTSP/    │ │          │  ┌─────────────┐ └──────┬───────┘   ┌────────────────┐   │
   │ │ ONVIF/   │ │          │  │   Redis     │ (dedup)│  alerts   │  Evidence       │   │
   │ │ GB28181 │ │          │  └─────────────┘        ▼           │  object store   │   │
   │ │ + YOLO/  │ │          │                    ┌───────────┐    └────────────────┘   │
   │ │   OCR    │ │          │  ┌──────────────┐  │ CORE API   │   ┌──────────────────┐ │
   │ │ InsightFace│ │         │  │   RECORDS    │  │ registry   │──▶│  OPERATOR WEB    │ │
   │ └──────────┘ │          │  │ CCTNS/VAHAN  │  │ watchlist  │   │  React + Leaflet │ │
   └──────────────┘          │  │ NAFIS enrich │  │ search     │   │  live alerts/GIS │ │
   ┌──────────────┐          │  └──────────────┘  │ auth/RBAC  │   └──────────────────┘ │
   │ SITE B       │  events  │  ┌──────────────┐  │ WebSocket  │                        │
   │ CP Plus NVR  │ ───────▶ │  │  NOTIFIER    │  └───────────┘                        │
   │ Dahua cams   │          │  │ SMS/email/   │              ┌──────────────────┐     │
   └──────────────┘          │  │ webhook/FCM  │              │  STREAMER         │     │
                              │  └──────────────┘              │  HLS · WebRTC     │     │
                              └──────────────────────────────────────────────────────┘
        one federated gateway pod per site; scales horizontally to 80,000 cameras
```

### 1.2 Services in this repository

| Service | Responsibility |
|---|---|
| `services/gateway` | Federation adapters (RTSP / ONVIF / HTTP-MJPEG / vendor-API / simulator), local detection + ANPR pipeline (YOLOv8n + RapidOCR), evidence snapshot capture, event publishing to NATS JetStream |
| `services/correlator` | Consumes event stream; persists events; builds cross-camera trajectories (session linking); watchlist matching (Redis-cached); alert generation with dedup; publishes alerts |
| `services/core_api` | FastAPI: camera registry CRUD, watchlist CRUD + bulk CSV import, event search, alert workflow (new/ack/resolve), tracking/route API, stats, JWT auth + RBAC, audit log, WebSocket alert fan-out, evidence file serving |
| `frontend` | React operator console: command dashboard, live map (cameras, alert pins, route trail), alerts, event search + CSV export, watchlist, camera registry |
| `packages/trinetra_core` | Shared domain models, plate normalization, DB schema (SQLAlchemy async), NATS bus helpers, trajectory session logic |
| `sim/` | Deterministic 50-camera scenario: heterogeneous vendors/VMS/protocols, scripted stolen-vehicle route, background traffic, anomaly events, rendered evidence frames |

### 1.3 Data flow (the mandatory test case end-to-end)

1. Gateway adapter observes vehicle at `CAM-002` → local pipeline detects vehicle + reads plate `GJ-01-KA-1234` (confidence 0.89) → renders evidence frame → publishes `DetectionEvent` to `trinetra.events.raw`.
2. Correlator persists the event, appends to the vehicle's trajectory session, and matches the normalized plate `GJ01KA1234` against the Redis-cached active watchlist → **STOLEN VEHICLE** hit.
3. Dedup guard (Redis `SET NX EX`) suppresses repeat alerts at the same camera; otherwise correlator writes an `AlertRow` and publishes `trinetra.alerts.new`.
4. Core API's WebSocket bridge fans the alert to every connected operator dashboard in real time; alert carries camera ID, coordinates, timestamp, confidence, and evidence frame.
5. Operator clicks **Track** → map fetches `/api/v1/tracking/GJ-01-KA-1234/route` → the correlator-assembled session renders as an ordered polyline across all 16 cameras the vehicle passes, updating live as subsequent cameras fire.
6. Event Search page exposes the full queryable history (plate/camera/time-range) with CSV export — the "searchable event log" requirement.

---

## 2. Integration Strategy (multi-vendor / multi-VMS / multi-protocol)

- **Canonical camera registry.** Every camera is a first-class record: ID, lat/long, vendor, VMS platform, protocol (`rtsp` | `onvif` | `http-mjpeg` | `vendor-api`), stream URI, status, department owner, zone. Analytics and GIS never talk to a camera directly — only to its registry entry. This is what absorbs heterogeneity.
- **Adapter-per-protocol gateway pods.** The gateway instantiates one adapter worker per protocol group. RTSP is the universal fallback (virtually every Indian CCTV estate exposes it); ONVIF resolves `GetProfiles`/`GetStreamUri` to an RTSP media URI then reuses the RTSP path; HTTP-MJPEG and vendor-API groups demonstrate the plugin surface for VMS-specific SDKs (Milestone/Genetec/CP Plus connectors are configuration, not re-architecture); **GB/T 28181** (SIP signaling + RTP/RTSP media) is the standardised interop path for the Hikvision/Dahua/CP-Plus estate dominant in India. See [`docs/INTEGRATION.md`](INTEGRATION.md).
- **Government records federation.** Records are federated like feeds: CCTNS/eGujCop auto-populates the watchlist (source-tagged); VAHAN/SARTHI/NAFIS enrich alerts in real time. The manual watchlist becomes a live, database-backed watchlist. See [`docs/INTEGRATION.md`](INTEGRATION.md) §2.
- **Normalized event schema.** Whatever the source, the bus carries one `DetectionEvent` schema (camera_id, ts, kind, plate + confidence, vehicle class/color/direction/speed, bbox, attributes, snapshot path). Downstream systems never see vendor formats.
- **Raw video stays at the site.** The WAN carries events + compressed evidence frames only; on-demand clip retrieval is a roadmap RPC over the same gateway. This is the difference between a demo that works on a laptop and a design that works on BharatNet links.
- **Ingestion of the government feed on-site** is a registry operation, not a code change: `POST /api/v1/cameras` with the provided RTSP/ONVIF URIs, restart the `gateway-ml` pod in `rtsp` mode. See `docs/DEMO_SCRIPT.md` §3.

---

## 3. AI & Video Analytics Architecture

| Stage | Component | Location | Rationale |
|---|---|---|---|
| Vehicle/object detection | YOLOv8n (COCO classes: car/motorcycle/bus/truck), conf ≥ 0.45 | Edge gateway | 6 MB model, runs on existing site hardware or a Jetson-class SoC; keeps video off the WAN |
| ANPR | RapidOCR (ONNX Runtime) on vehicle crops + Indian plate regex | Edge gateway | Pure-pip, CPU-viable, no system Tesseract dependency; GPU profile accelerates via CUDA build |
| Anomaly detection | Gateway-side rules (crowd formation, unattended object) raising `anomaly` events | Edge gateway | Deployable day-1 heuristic; upgradeable to temporal models (roadmap) |
| Watchlist matching | Exact normalized-plate match against Redis-cached active set; sub-ms per event | Central | Deterministic, explainable, zero false positives on plates; fuzzy/Levenshtein match is a config flag |
| Cross-camera tracking | Session linking: same normalized plate within a 60-min gap window = one trajectory session; ordered by timestamp | Central correlator | No Re-ID ML needed for the plate-carrying case; vehicle-embedding Re-ID for plate-miss cases is phase-2 |
| Alert quality | Confidence surfaced on every alert; Redis dedup window (60 s per watchlist-entry × camera) | Central | Directly answers the "false-positive handling" evaluation criterion |
| Records enrichment | On a plate hit, VAHAN vehicle/owner + SARTHI DL attached to the alert; CCTNS source + FIR ref on every watchlist-sourced alert; NAFIS for persons | Central (correlator + records service) | Turns alerts into actionable dossiers; auto-populated watchlist removes manual lag |
| Facial Recognition (FRS) | YuNet face detector (OpenCV `FaceDetectorYN`) at the edge → correlator matches the detected face via the NAFIS connector → wanted/missing-person alert with FIR ref + NAFIS score; production upgrades to ArcFace/InsightFace embeddings + FAISS/Milvus gallery behind the same seam | Edge (detect) + Central (match) | Same edge/center split as ANPR; delivered with the YuNet detector + NAFIS connector (mock for demo; real embeddings drop in). The `AnalyticsEngine` ABC lets a deeper face engine swap in without touching the adapter or bus |
| Person/vehicle tracking | Plate-keyed session linking (day-1); vehicle-embedding Re-ID (phase-2) stitches trajectories when ANPR misses; Kalman/ByteTrack at junctions for direction+speed without ANPR (roadmap) | Central correlator | No Re-ID ML needed while plates are visible; Re-ID covers the plate-miss gap |

**Edge vs. cloud decision:** detection and OCR at the edge (bandwidth + latency), correlation and search centrally (state). At statewide scale, <20% of cameras warrant GPU at the edge (high-flow junctions); the rest run CPU-quantized YOLOv8n at 2–5 fps detection cadence — see `docs/SCALABILITY.md`.

### 3.1 Pluggable analytics engine (AI modules replaceable)

Analytics is behind the `AnalyticsEngine` ABC (`packages/trinetra_core/analytics.py`). The default `AnalyticsPipeline` (YOLOv8n + RapidOCR) is one implementation; a `MockAnalyticsEngine` is provided for CPU-less test environments; a future FRS/Re-ID or vendor-SDK engine drops in behind the same interface and is selected via `TRINETRA_ANALYTICS_ENGINE`. Neither the adapter, the event-bus schema, nor the correlator change when the engine is swapped — directly satisfying the RFP's "AI modules replaceable without redesign" principle. See `docs/ARCHITECTURE_PRINCIPLES.md`.

---

## 4. Cybersecurity Architecture (summary — full detail in `docs/SECURITY.md`)

- OAuth2 password-flow → signed JWT (HS256, rotating secret via env), 12 h operator sessions.
- RBAC: `admin` (full + audit + registry), `analyst` (watchlist + search), `operator` (monitor, ack/resolve alerts). Enforced server-side per-route; UI merely reflects it.
- Immutable audit trail: every mutation (watchlist CRUD, alert status, camera changes, imports, logins) recorded with user/action/entity/details.
- TLS everywhere in production deployment (nginx/ingress termination, Postgres/NATS/Redis on isolated overlay networks — never host-published except the API/UI edges).
- PII discipline: watchlist entries carry purpose + FIR reference; evidence retention policy (roadmap: auto-expiry per DPDP Act 2023 and GPDPL norms); plates stored in normalized + display forms to keep search deterministic.
- Secrets via environment injection; the repo ships only dev defaults.

---

## 5. Deployment Architecture

- **Pilot (this repo):** Docker Compose — `postgis/postgis:16-3.4`, `redis:7`, `nats:2.10` (JetStream, file storage), three Python services, React build served by nginx. Single `scripts/demo.ps1` brings up the full stack including the 50-camera scenario. GPU profile (`--profile gpu`) builds the gateway with CUDA inference for live RTSP.
- **District/state:** same images on Kubernetes — correlator and core-api as Deployments (HPA on queue depth / CPU), gateways as DaemonSets on site nodes, NATS cluster (3-node) or managed Kafka swap-in, Postgres with streaming replica + PgBouncer, evidence on S3-compatible object storage. Helm chart + GitOps is roadmap item #1 post-hackathon.
- **Hybrid posture:** control plane may run in a state data centre or on-prem cloud (no public SaaS dependency — a police requirement); gateways always run on-site.
- **Operations:** the full central/regional/edge compute, GPU, bandwidth, storage-tier, scaling/monitoring, HA/DR/security, and cost detail is in [`docs/DEPLOYMENT_AND_OPERATIONS.md`](DEPLOYMENT_AND_OPERATIONS.md).

---

## 6. Infrastructure Sizing

**Pilot (50 cameras, demo-grade):** 1 laptop/VM, 8 vCPU / 16 GB RAM / 100 GB disk. Runs the entire stack plus simulated 50-camera load with headroom.

**District (~2,000 cameras):** 1 gateway pod per 16–32 cameras (x86 mini-PC or existing NVR-adjacent server, 4 cores/8 GB each — ~80 pods), central: 3 app nodes (16 vCPU/64 GB), Postgres primary + replica (32 vCPU/128 GB/2 TB NVMe), NATS 3-node cluster, 2× L4 GPU nodes for optional central re-processing/face roadmap.

**Statewide (80,000):** see `docs/SCALABILITY.md` for the full derivation — ~3,200 gateway pods, ~24 central app nodes, Postgres sharded by zone with a federal query layer, ~20 L4-class GPU nodes for embedding/Re-ID services, ~250 TB tiered storage.

---

## 7. Cost-Benefit Analysis (summary — full detail in `docs/COST_BENEFIT.md`)

Pilot CAPEX ≈ ₹6–9 L (existing cameras reused; compute + integration effort), state rollout ≈ ₹95–140 Cr CAPEX + ₹18–25 Cr/yr OPEX over 5 years — versus manual monitoring of 80,000 feeds being impossible at any price, and each hour saved in vehicle-theft recovery measurably improving recovery rates. The federated design avoids the ~₹400 Cr+ WAN and data-centre cost that raw-stream centralization would impose.

---

## 8. Department-wise Information Requirements

| Unit | Needs | Served by |
|---|---|---|
| State Control Room / PHQ | Statewide alert feed, force-wide stats, audit access | Dashboard, stats API, audit log (admin) |
| Traffic Police | Vehicle/plate search, blacklisted vehicle alerts, camera status by zone | Event search, watchlist (analyst), registry |
| Crime Branch / CI | Watchlist management, trajectory history, evidence export | Watchlist CRUD/import, tracking API, CSV export |
| Local PS / DCP offices | Alerts scoped to their zone cameras | Zone-filtered camera registry + alert filters |
| Cyber/Railways/GRP | Event log queries, anomaly alerts, chain-of-custody audit | Event search, anomaly alerts, audit trail |
| IT/Nodal officers | Camera onboarding, health, protocol/firmware metadata | Registry CRUD + status |

RBAC maps these to the three seeded roles plus per-zone scoping (roadmap: zone-level row security in Postgres, already prepared by the `zone` column).

### 8.1 Department tenancy (26 departments)

The registry models all 26 government departments as first-class records, each with its own **event/evidence retention policy** (7/15/30 days, reflecting the heterogeneity in the field). Users are department-scoped: a Traffic or RTO operator sees only their own department's cameras, alerts, and events (`apply_scope` enforced server-side on every list query; admins are global). A `janitor` service enforces per-department retention (dry-run by default). Private/community cameras onboard with `source_type=community` + explicit consent and a restricted scope.

---

## 9. Scalability Strategy (summary — full detail in `docs/SCALABILITY.md`)

Bandwidth math is the headline: 80k × 4 Mbps raw ≈ **320 Gbps** (infeasible) vs. event-plane ≈ **1–2 Gbps average** for the same estate. Gateways scale horizontally (one per site), the bus clusters (NATS → Kafka at district scale), Postgres shards by zone, inference scales at the edge where the cameras are. Phased rollout: 50-camera pilot → district (2k) → range (10k) → state (80k).

---

## 10. Delivered in this build vs. Future Roadmap

**Delivered (runnable in the demo):**

- **Government records integration** — CCTNS auto-watchlist + VAHAN/SARTHI/NAFIS enrichment (mock connectors; real drop in behind the same ABCs).
- **Live viewing** — on-demand HLS per camera + optional WebRTC/WHIP; community-camera self-service onboarding with consent.
- **Real-time alert fan-out** — SMS/email/webhook(CCTNS)/FCM routing with a notifications audit panel.
- **26-department governance** — department-scoped RBAC + per-department retention + janitor enforcement.
- **GB/T 28181** standardised camera interop adapter.
- **Face detection & recognition** — YuNet face detector in the pipeline → NAFIS connector match → wanted/missing-person alerts (verified on live grid feeds).
- **AsyncAPI** event-bus contract.

**Future roadmap:**

1. **Face-embedding watchlist matching** (ArcFace/InsightFace at edge, FAISS/Milvus central) for wanted/missing persons — schema already supports person entries; NAFIS connector seam ready.
2. **Vehicle Re-ID across plate-miss frames** (embedding-based) to stitch trajectories when ANPR fails.
3. **On-demand clip retrieval RPC** through the gateway for post-event evidence collection.
4. **Kafka + Kubernetes/Helm productionization**, zone-sharded Postgres, S3 evidence lifecycle policies.
5. **Kalman/ByteTrack multi-object tracking at junctions** for direction + speed without ANPR.
6. **Real SMS/email/FCM gateways + mobile alert app** (the routing + audit are live; gateways are config); one-click CCTNS/FIR case linkage.
7. **Fuzzy plate matching (edit-distance ≥ 0.9)** behind a confidence threshold, and per-camera health scoring.
8. **Postgres row-level security per department** (the `apply_scope` seam is ready; RLS is the production hardening).

---

## 11. Alert Prioritisation, Visualisation & User Interaction

- **Prioritisation by category.** Alerts carry a category (`stolen_vehicle`, `blacklisted_vehicle`, `wanted_person`, `missing_person`, `suspect`, `anomaly`) which maps to a severity and a routing policy in the `notifier` (e.g., `stolen_vehicle` → SMS to DCP + CCTNS webhook + FCM to traffic field units; `wanted_person` → SMS + email to Crime Branch + CCTNS webhook). Category + confidence + source (CCTNS-sourced hits rank above heuristic anomalies) drive the on-screen ordering and colour-coding.
- **Deduplication.** A Redis `SET NX EX` window (60 s per watchlist-entry × camera) suppresses repeat alerts at the same camera so operators see one actionable alert per event, not a flood.
- **Visualisation.** The operator console surfaces alerts four ways: (1) the dashboard live-feed (cards with evidence frame, source badge, VAHAN enrichment), (2) the live map with red alert pins, (3) the alerts table (status workflow new→ack→resolved), and (4) real-time WebSocket push. The camera-grid mosaic + live view let operators visually confirm a detection.
- **User interaction.** Operators Ack/Resolve alerts (audited); analysts manage the watchlist (CRUD + CSV import) and search the event log (plate/camera/time + CSV export) for investigation; admins manage the registry, departments, and retention. RBAC scopes each role; department-scoped users see only their own cameras/alerts.
- **Fan-out.** Every alert is fanned to configured channels (SMS/email/webhook/FCM) with a delivery audit (the Notifications panel), so field units receive alerts even when not at a console.

---

## 12. Technical Prerequisites, Assumptions & Information Required from Departments

**Assumptions**
- Existing cameras/NVR/VMS remain in place (no rip-and-replace); the platform federates through standard protocols.
- A state WAN (police/BSNL) connects sites to the State Data Centre; site gateways use outbound-only connections.
- Per-department retention (7/15/30 days) is policy-configurable; raw video stays on-site on existing NVR storage.

**Technical prerequisites (per site)**
- A gateway pod (x86 mini-PC / NVR-adjacent server / Jetson for GPU sites) per 16–32 cameras, 4 cores / 8 GB RAM / 256 GB SSD, LAN-adjacent to the cameras.
- RTSP/ONVIF/GB28181 access to the cameras (credentials + stream URIs); for VMS-bridged sites, the VMS SDK/event-stream access.
- Outbound network reach from the site gateway to the district/state event bus (NATS/Kafka) — no inbound firewall pinholes.

**Information required from each participating department** (to assess integration feasibility + interoperability)
1. **Camera inventory** — per camera: id, location (lat/lon), vendor, model, VMS platform, protocol (RTSP/ONVIF/GB28181/vendor-API), stream URI, resolution/codec, connectivity, ownership, retention currently configured. (Bulk-importable via the registry CSV template — `POST /api/v1/cameras/import`.)
2. **VMS / NVR details** — vendor, version, whether it exposes an event/stream API (Milestone/Genetec/CP-Plus SDK), AMC status, storage architecture.
3. **Network** — site LAN topology, available bandwidth to the district/State DC, existing VLANs, whether outbound to the state WAN is permitted.
4. **Watchlist data** — for CCTNS/eGujCop integration: API access or a feed of stolen/wanted/missing/blacklisted records (with FIR references); for VAHAN/SARTHI/NAFIS: API access + service accounts. (The connector ABCs are ready; real access drops in behind them.)
5. **Department tenancy** — department code, owner/contact, retention policy, scoped users/roles.
6. **Operational** — zones/areas of responsibility, alert routing recipients (DCP/PS/field-unit contacts + channels), existing SOPs for alert handling.

**Interoperability assurance** — onboarding is a registry operation (manual entry / bulk CSV / API), not a code change; the normalised `DetectionEvent` schema + AsyncAPI bus contract mean any conforming camera/department integrates identically. GB/T 28181 + ONVIF cover the dominant Hikvision/Dahua/CP-Plus estate; the adapter registry accepts new vendor/protocol adapters without redesign.
