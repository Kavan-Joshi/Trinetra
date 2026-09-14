# Trinetra — Integrated Video Management & Analytics Platform

Federated CCTV integration + real-time AI watchlist matching + government-database enrichment + GIS vehicle tracking + live viewing, built for the **Gujarat Police Innovation Challenge 2026** and the State CCTV Integration RFP.

**Architecture thesis:** *detect at the edge, correlate at the center, move events not video.* Gateway adapters (RTSP / ONVIF / HTTP-MJPEG / vendor-API / **GB/T 28181**) run detection locally and publish structured events + evidence frames to a central correlator that does watchlist matching (auto-populated from **eGujCop/CCTNS**), cross-camera trajectory stitching, **VAHAN/SARTHI/NAFIS** enrichment, alerting, and fan-out. Raw video never crosses the WAN — which is what makes 80,000-camera scale a networking non-event (~1–2 Gbps event plane vs ~320 Gbps for raw centralization). Design docs: [`docs/HLD.md`](docs/HLD.md) · [`docs/INTEGRATION.md`](docs/INTEGRATION.md) · [`docs/SCALABILITY.md`](docs/SCALABILITY.md) · [`docs/SECURITY.md`](docs/SECURITY.md) · [`docs/asyncapi.yaml`](docs/asyncapi.yaml).

## Quickstart (the full demo, one command)

```powershell
cd C:\Projects\sentinel-gujarat
.\scripts\demo.ps1
```

Brings up PostGIS, Redis, NATS JetStream, core API, correlator, **records** (CCTNS sync), **notifier** (alert fan-out), **streamer** (live HLS/WebRTC), **janitor** (retention), event gateway, seeder (50 govt cameras + 3 community cameras + 26 departments + watchlist + users), and the operator console. Browser opens at **http://localhost:8080**.

- **Login:** `admin / admin123` (also `operator`, `analyst`, `traffic`, `rto`, `fcs` — the last three are department-scoped)
- **API docs:** http://localhost:8000/docs
- The stolen black Creta **GJ-01-KA-1234** starts moving ~15 s after startup; its 16-camera trail completes in ~75 s at default 20× playback, with alerts carrying CCTNS source + VAHAN enrichment.

## What each part does

| Path | Role |
|---|---|
| `services/gateway` | Federation adapters (RTSP/ONVIF/HTTP-MJPEG/vendor-API/**GB28181**) + YOLOv8/RapidOCR pipeline; simulator plays the deterministic 50-camera scenario |
| `services/correlator` | Event persistence, trajectory session linking, watchlist matching, **VAHAN/SARTHI enrichment**, alert generation + dedup |
| `services/core_api` | Registry (manual/bulk-JSON/CSV/API onboarding), watchlist (CRUD + CSV import), event search, alerts workflow, tracking API, **records dossier lookup**, **departments + retention**, **gap analysis (coverage + ageing)**, **camera health**, **community onboarding**, **notifications**, **CSV export**, JWT/RBAC (department-scoped), audit, WebSocket fan-out |
| `services/records` | **Government DB integration layer** — auto-syncs CCTNS/eGujCop stolen/wanted/missing feeds into the watchlist (source-tagged); plate/person dossier API (VAHAN/SARTHI/CCTNS/NAFIS) |
| `services/notifier` | **Real-time alert fan-out** — routes alerts by category to SMS / email / webhook (CCTNS) / FCM mobile push; records every dispatch |
| `services/streamer` | **Live viewing** — on-demand HLS (ffmpeg) per camera + optional WebRTC/WHIP (sub-second); sim mode generates test-pattern feeds |
| `services/janitor` | Per-department retention enforcement (dry-run by default) |
| `frontend` | React + Leaflet operator console (dashboard, live map + trail, **live view player**, alerts, fan-out, event search + CSV, watchlist, cameras, **records lookup**, **departments**, **community onboarding**) |
| `sim/` | 50-camera Ahmedabad→Gandhinagar corridor (8 vendors, 6 VMS, 5 protocols), scripted route, background traffic, anomalies, mock government DB records, 3 community cameras |
| `packages/trinetra_core` | Shared domain models, plate normalization, DB schema, NATS bus, trajectory logic, **records connectors** |
| `scripts/` | `demo.ps1` (fresh bring-up), `replay.ps1` (scenario replay), `seed.py` (idempotent seeder: 26 depts + cameras + watchlist + users), `ingest_catalogue.py` (onboard the real live grid from `cameras.json`) |
| `tests/` | Unit tests for plates, trajectory, scenario, governance, records connectors |

## Live feeds (provided camera grid / real RTSP)

The platform consumes the provided live grid (RTSP/HLS/WebRTC). Put your grid credentials in `.env` (`TRINETRA_GRID_EMAIL` / `TRINETRA_GRID_PASSWORD`), then:

```powershell
docker compose --profile grid run --rm ingester          # onboard cameras.json into the registry
docker compose --profile gpu up -d --build gateway-ml    # GPU inference gateway pulls RTSP over TCP
$env:TRINETRA_STREAMER_MODE="live"; docker compose up -d --build streamer  # live HLS viewing
```

The gateway's `RTSPAdapter` follows the grid consumption contract: forces TCP, reconnects with exponential backoff (2 s → 30 s), tolerates inter-frame gaps, drives timing from PTS, and recovers from scene loop-cuts. Full details: [`docs/GRID_FEEDS.md`](docs/GRID_FEEDS.md).

Full on-site procedure: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) §3.

## WebRTC (sub-second live view)

```powershell
docker compose build --build-arg INSTALL_WEBRTC=true streamer
```

## Verification

```powershell
python -m compileall packages services sim scripts   # syntax check all Python
python -m pytest tests -q                            # plate + trajectory + governance + records tests
npx tsc --noEmit                                     # frontend typecheck (in frontend/)
```

## Demo runbook & submission docs

[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — minute-by-minute judge flow, government-feed swap, failure playbook · [`docs/HLD.md`](docs/HLD.md) — full High-Level Design · [`docs/INTEGRATION.md`](docs/INTEGRATION.md) — records/GB28181/community/viewing integration · [`docs/PRESENTATION_OUTLINE.md`](docs/PRESENTATION_OUTLINE.md) — PPT + demo-video script.
