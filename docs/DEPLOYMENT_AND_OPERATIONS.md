# Trinetra — Deployment & Operations

Explicit treatment of the seven operational areas the submission must explain. Cross-references the detailed docs (`SCALABILITY.md`, `SECURITY.md`, `COST_BENEFIT.md`); figures are planning-grade (±30%) for an ~80,000-camera statewide estate and a 50-camera pilot.

## 1. Central, regional, and edge-compute requirements

Three tiers, each scaling independently.

**Edge (site / camera cluster)** — *where detection happens.*
- 1 gateway pod per 16–32 cameras. Spec: 4 vCPU / 8 GB RAM / 256 GB SSD (x86 mini-PC or NVR-adjacent server); Jetson Orin Nano (~15 W) for high-flow GPU sites. Software: the gateway container in this repo, CPU-quantized YOLOv8n @ 2–5 fps detection cadence + RapidOCR ANPR.
- ~3,200 gateway pods statewide (64,000 cameras on CPU pods; 16,000 high-flow junction cameras on GPU pods).
- Role: pull RTSP/ONVIF/GB28181 locally (LAN-speed), run detection + ANPR, publish structured events + evidence frames to the bus. Raw video never leaves the site.

**Regional (range / district DC)** — *aggregation + relay.*
- Per range: a 3-node NATS JetStream cluster (or 3-broker Kafka where IT policy prefers it) for durable event transit; a district correlator + Redis cache; a local warm-storage tier.
- ~80 gateway pods feed each district DC; the district relays aggregated events to the State DC. District nodes: 4 app nodes (16 vCPU/64 GB) + 1 Postgres read-replica for local queries.

**Central (State Data Centre)** — *statewide correlation, records, search, alerting.*
- App tier: ~24 nodes (16 vCPU/64 GB) running correlator + core-api + records + notifier, autoscaled on queue depth/CPU behind nginx/ingress.
- Databases: PostgreSQL 16 + PostGIS, sharded by zone (4 shards + 1 federal query node), each primary + streaming replica; Redis Sentinel pair per shard.
- Bus: NATS cluster (3-node) or managed Kafka. Object storage: ~250 TB tiered (hot NVMe / object / archive).
- GPU: ~20 L4-class nodes for phase-2 embedding services (face/Re-ID) — **not** required for day-1 ANPR.

## 2. GPU / accelerator requirements for video analytics

- **Edge:** <20% of cameras warrant GPU at the edge — only high-flow junctions where full-rate, multi-lane ANPR justifies it. Those sites use Jetson Orin Nano / Orin NX (~15–25 W). The remaining ~80% run CPU-quantized YOLOv8n at 2–5 fps detection cadence (≈30 ms/frame on 4 modern cores) — sufficient for ANPR at junction cadence and far cheaper.
- **Central:** ~20 L4-class (24 GB) GPU nodes serve *phase-2* embedding search (face/Re-ID) over event clips — a bounded, back-pressure-friendly workload (clips, never raw streams). Day-1 ANPR needs **zero** central GPU.
- **Accelerator-agnostic:** inference runs on ONNX Runtime / Ultralytics, so the same models deploy on CPU, NVIDIA CUDA, or Jetson — no lock-in. The `AnalyticsEngine` ABC lets a future accelerator-backed engine drop in without code change.

## 3. Expected network bandwidth & low-bandwidth strategies

| Plane | Per-camera | 80,000 cameras | Feasible? |
|---|---|---|---|
| Raw video centralised (rival design) | 4 Mbps continuous | **~320 Gbps** + ~86 PB/yr | No |
| **Trinetra event plane** (events + evidence frames) | ~30 events/day, 1 KB event + ~100 KB snapshot | **~1–2 Gbps average**, ~240 GB/day evidence | **Yes** |

- **Site → district:** ≤2 Mbps sustained per gateway (events + snapshots, bursty) — fits existing police WAN/BSNL links. **Store-and-forward:** JetStream (file storage) + on-disk buffer ride out link outages; events replay on reconnection, nothing lost.
- **District → State DC:** ~40 Gbps aggregate event-plane budget statewide with 10× headroom — ordinary DWDM/leased capacity.
- **Low-bandwidth strategies:** (1) detect at the edge so only O(events) cross the WAN; (2) on-demand viewing — an operator pulls a stream only while watching (no continuous central ingestion); (3) adaptive detection cadence (drop to 2 fps on poor links); (4) evidence-frame JPEG compression; (5) QoS marking — event plane AF41, clip-retrieval best-effort; (6) government/VMS VLANs untouched (gateways sit alongside NVRs and pull RTSP on the LAN).
- Government/VMS VLANs untouched (gateways pull RTSP on the LAN — no change to current camera networking).

## 4. Hot / warm / cold storage assumptions (by retention period)

| Data class | Volume @80k | Retention | Tier | Store |
|---|---|---|---|---|
| Event metadata | ~2.5 GB/day → ~5 TB | 5 years | **Hot** | Postgres (sharded) — fast query |
| Evidence frames | ~240 GB/day → ~22 TB | 90 days | **Hot→Warm** | Object storage, NVMe 30 d / object 60 d |
| Event clips (roadmap) | ~5 TB/day → ~150 TB | 30 days | **Warm** | Object storage, erasure-coded |
| Audit log | <1 GB/day | 7 years | **Hot (WORM export)** | Postgres + immutable export |
| Raw video | — | 7/15/30 days per dept (status quo) | **Cold (on-site)** | Existing NVR — **never centralised** |

- Per-department retention (7/15/30 days) is policy-configurable per `DepartmentRow`; the `janitor` service enforces it (dry-run by default). Object-storage lifecycle policies tier evidence hot→object→archive; raw video stays on-site on existing NVR storage (the status quo).

## 5. Load balancing, horizontal scaling, monitoring, logging, health checks

- **Load balancing:** nginx/ingress terminates client TLS and load-balances core-api; correlator instances share work via JetStream **queue groups** (each event delivered to exactly one correlator); gateways are independent (no coordination needed).
- **Horizontal scaling:** gateways scale by adding pods (one per site); correlator/core-api/records/notifier scale by adding replicas (HPA on queue depth / CPU); Postgres scales by sharding (zone); NATS/Kafka by adding cluster nodes. No component is a singleton except the DB primary (mitigated by replica + failover).
- **Monitoring & metrics:** structured JSON logs; Prometheus metrics — events processed, alert latency (p95), queue depth, per-camera health (online/degraded/offline), gateway emit counts; Grafana dashboards for the control room. Per-camera health scoring is a roadmap item; basic status is live.
- **Logging:** append-only audit log (every mutation: actor/action/entity/details) for non-repudiation; service logs shipped to a central log store.
- **Health checks:** Docker `HEALTHCHECK` on postgres/redis; `/health` endpoints on core-api, records, streamer; gateway adapter heartbeats (emit-count logging every 50 events); camera `status`/`health`/`last_heartbeat` in the registry, surfaced on the GIS map + Cameras page.

## 6. High availability, backup, disaster recovery & cybersecurity controls

**High availability & DR**
- **RPO 15 min / RTO 1 h** for the control plane. Postgres WAL streaming to a second DC; NATS JetStream 3-copy replication + mirror to DR; object storage cross-DC erasure/replication.
- Stateless services (correlator/core-api/records/notifier) run multi-instance behind the bus/ingress; Postgres primary + streaming replica with automatic failover; Redis Sentinel; NATS 3-node cluster.
- Sites are failure-isolated: a dead gateway takes only its cameras dark; buffered events replay on recovery (store-and-forward). Quarterly DR drills; gateway images are immutable and re-deployable from a district registry mirror.

**Cybersecurity controls** (detail in `SECURITY.md`)
- Identity: OAuth2 → JWT (HS256 dev / RS256+JWKS prod), 12 h sessions; **department-scoped RBAC** enforced server-side on every route.
- Audit: immutable `audit_log` for every mutation; alert lifecycle (new→ack→resolved) audited; records-lookup chain-of-custody (actor, system, plate/person, FIR ref).
- Transport/network: TLS 1.2+ everywhere; service-to-service on isolated overlay networks; site gateways **outbound-only** (no inbound pinholes to police sites); mTLS + service accounts for CCTNS/VAHAN/NAFIS connectors.
- Data: at-rest encryption (LUKS/cloud KMS) for Postgres + evidence; PII discipline (watchlist entries carry purpose + FIR ref; plates in normalized + display forms; biometric templates isolated if/when stored); retention per DPDP Act 2023 / GPDPL.
- App security: Pydantic input validation on every boundary; parameterized SQL only (no string SQL); WebSocket token auth; rate-limiting on login (roadmap: per-IP+per-user lockout); secrets via env/Vault injection (repo ships dev defaults only).
- Threat model: rogue-feed rejection (events from unregistered cameras dropped + logged), alert tamper-resistance (append-only rows + audited status changes), gateway blast-radius limited (holds only a bus credential), DoS absorption (JetStream persistent queues + dedup windows).

## 7. Estimated implementation & operational costs

**Pilot (50 cameras):** CAPEX ≈ ₹6–9 L (2× mini-PC gateway ₹1.5 L; central VM ₹2.5 L; integration/survey/training ₹2–4 L). Near-zero incremental OPEX (existing police WAN + rack space).

**Statewide (80,000 cameras, 5-year horizon):**

| Item | Estimate |
|---|---|
| 3,200 gateway pods (CPU/GPU mix, incl. install) | ₹28–38 Cr |
| Central DC: 24 app nodes + DB tier + 20 GPU nodes + networking | ₹22–30 Cr |
| Control-plane services (records/notifier/janitor/streamer; shares app tier; streamer on-site) | ₹1–2 Cr |
| Storage 250 TB tiered + DR site | ₹10–15 Cr |
| Site surveys, cabling-to-gateway, project management (33 districts) | ₹25–35 Cr |
| **Total CAPEX (5-year)** | **₹95–140 Cr** |
| Annual OPEX (power, links, maintenance, staff) | ₹18–25 Cr/yr |

**Avoided cost:** centralising raw streams would need ~320 Gbps dedicated WAN + ~86 PB/yr — **₹400 Cr+** in network and storage alone, before any AI. Trinetra's federated event plane runs on the existing WAN at 1–2 Gbps.

**Benefits (qualitative):** force multiplication (one operator effectively monitors thousands of feeds), faster stolen-vehicle recovery, investigation hours saved (plate/camera/time search in minutes), interoperability dividend, zero vendor lock-in. Detail in `COST_BENEFIT.md`.
