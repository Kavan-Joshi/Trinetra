# Trinetra — Scale to 80,000 Cameras (Statewide Plan)

## 1. The Bandwidth Thesis (why this architecture scales)

| Plane | Per-camera load | 80,000 cameras | Feasible? |
|---|---|---|---|
| Raw video centralized (typical rival design) | 4 Mbps continuous | **~320 Gbps** + ~86 PB/yr storage | No — this is why "central VMS for everything" fails |
| Trinetra event plane (structured events + evidence frames) | ~30 events/day avg, 1 KB event + ~100 KB snapshot | **~1–2 Gbps average**, ~240 GB/day evidence | Yes — fits a state WAN with headroom |

Design rule: **move O(events), not O(video)**. Detection runs at the site gateway; the WAN never carries continuous video. On-demand clip retrieval (roadmap) pulls a 10 s clip only when an operator requests it. Live viewing (HLS/WebRTC) is similarly on-demand and operator-bounded — a stream exists only while someone watches, so even at 80k cameras the viewing plane is bounded by concurrent operators, not camera count.

## 2. Hardware & Software at Statewide Scale

**Edge / site layer (~3,200 gateway pods):**
- 1 gateway pod per 16–32 cameras (x86 mini-PC / NVR-adjacent server / Jetson Orin Nano for GPU sites).
- Spec: 4 cores, 8 GB RAM, 256 GB SSD (snapshot buffer). Software: same gateway container as the pilot (this repo), CPU-quantized YOLOv8n @ 2–5 fps detection cadence.
- ~64,000 cameras on CPU gateways; ~16,000 high-flow junction cameras on GPU gateways (real-time multi-lane ANPR).

**Central layer (state data centre):**
- App tier: ~24 nodes (16 vCPU/64 GB) running correlator + core-api with autoscaling on queue depth.
- Bus: NATS 3-node cluster per range; or Kafka (3 brokers/range) where IT policy prefers it — the publish/subscribe seams are already isolated in `trinetra_core.bus`.
- Databases: Postgres sharded by zone (4 shards + 1 federal query node), each primary + streaming replica; Redis Sentinel pair per shard.
- GPU: ~20 L4-class nodes for phase-2 embedding services (face/Re-ID) — not required for day-1 ANPR operation.
- Object storage: ~250 TB tiered (hot NVMe 30 d / object 90 d / archive 5 yr).
- **New control-plane services** (statewide): `records` (CCTNS sync + dossier lookups) and `notifier` (fan-out) scale horizontally with the app tier — a few pods each, cached behind Redis; `janitor` is a singleton-per-shard cron. The `streamer` runs **on site** (one per gateway pod) since it pulls local RTSP — viewing bandwidth is on-demand and bounded by the number of concurrent operators, not the camera count.

## 3. Network & Bandwidth Planning

- Site → district: ≤ 2 Mbps sustained per gateway (events + snapshots, bursty), fits on existing police WAN/BSNL links; store-and-forward buffer (JetStream + disk) rides out outages.
- District → state DC: aggregate ~40 Gbps statewide event plane budget with 10× headroom — ordinary DWDM/leased capacity.
- Government/VMS VLANs untouched: gateways sit alongside existing NVRs and pull RTSP locally (LAN-speed), so no change to current camera networking.
- QoS: event plane marked AF41; clip retrieval best-effort.

## 4. Storage & Retention Strategy

| Data class | Volume estimate @80k cams | Retention | Store |
|---|---|---|---|
| Event metadata | ~2.4 M events/day ≈ 2.5 GB/day | 5 years (~5 TB) | Postgres (sharded) |
| Evidence frames | ~240 GB/day | 90 days (~22 TB) | Object storage, lifecycle-tiered |
| Event clips (roadmap) | ~2.4 M × 2 MB/day ≈ 5 TB/day | 30 days (150 TB) | Object storage, erasure-coded |
| Raw video | **never centralized** | 30 days on-site NVR (status quo) | Existing NVR storage |
| Audit log | <1 GB/day | 7 years | Postgres, WORM export |

## 5. AI Processing Capacity Planning

- Edge CPU: YOLOv8n @ 2 fps ≈ 30 ms/frame on 4 modern cores → one gateway handles 16–32 cameras comfortably at detection cadence.
- Edge GPU (Jetson Orin Nano, ~15 W): full-rate ANPR on 8–16 streams.
- Central GPUs (~20 L4): serve *phase-2* embedding search (face/vehicle Re-ID) on event clips only — a bounded, back-pressure-friendly workload, never raw streams.
- Load balancing: gateways are independent (no coordination), correlator scales horizontally via JetStream queue groups (one event → one correlator instance).

## 6. Disaster Recovery

- **RPO 15 min / RTO 1 h** for the control plane: Postgres WAL streaming to a second DC; NATS JetStream data replicated (3 copies) and mirrored to DR; object storage cross-DC erasure/replication.
- Sites are failure-isolated: if a site's gateway dies, only that site goes dark; its cameras' buffered events replay on recovery (store-and-forward).
- Quarterly DR drills; gateway images are immutable and re-deployable from the district registry mirror.

## 7. Statewide Rollout Plan (phased)

| Phase | Scope | Duration | Exit criteria |
|---|---|---|---|
| 0 — Pilot | 50 heterogeneous cameras (this repo's test case) | 4–6 weeks | Mandatory test case executed live; SOC operator training |
| 1 — District | 1 district (~2,000 cams, ~80 gateways) | 1 quarter | Alert latency < 3 s p95; false-positive rate < 2%; WAN utilization < 30% |
| 2 — Range | 4 ranges (~10,000 cams) | 2 quarters | Sharded Postgres + DR drill passed; CCTNS/FIR integration live |
| 3 — State | 80,000 cams, all 33 districts | 4–6 quarters | Full estate onboarded via registry; legacy VMS untouched |

Each phase reuses the pilot's images and adapters — scale is an operations exercise (site surveys, gateway install, registry onboarding), not a re-architecture.
