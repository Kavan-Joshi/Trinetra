# Trinetra — Solution Presentation Outline

*Maps directly to the 8 required content areas. Suggested length: 12–14 slides + a 3-minute demo video. Submission as PDF/PPT.*

## Slide deck

1. **Title** — Trinetra · Integrated Video Management & Analytics · team · challenge · one-line thesis: *"We move events, not video."*

2. **Proposed solution model + justification** *(Area 1)* — **Hybrid: Reference Model 1 (Registry & GIS foundation) + Model 3 (VMS-federation middleware) + Model 2 (Unified viewing & analytics)**, unified by "detect at the edge, correlate at the center." Justification: 80,000 already-deployed cameras across incumbent VMS cannot be replaced; raw centralisation is 320 Gbps—infeasible; pure middleware delivers no AI value. Trinetra federates feeds through edge gateways, runs detection/ANPR locally, and centralises only watchlist matching, trajectory correlation, records enrichment, and alerting. *(HLD §0)*

3. **Solution overview, objectives & key innovations** *(Area 2)* — objectives (unify 26 departments' CCTV, correlate with VAHAN/CCTNS/NAFIS, real-time alerts); innovations: O(events) scaling thesis, CCTNS-auto-populated watchlist, VAHAN-enriched alerts, pluggable AnalyticsEngine + AdapterRegistry, on-demand live viewing.

4. **High-level architecture & end-to-end workflow** *(Area 3)* — gateway adapters (RTSP/ONVIF/GB28181/vendor) → NATS event bus → correlator → PostgreSQL/PostGIS → alerts/GIS/search; the "detect-edge / correlate-center" diagram (HLD §1.1); the 6-step data flow (HLD §1.3).

5. **AI-powered video analytics** *(Area 4)* — YOLOv8n vehicle/object detection, RapidOCR ANPR (Indian-plate regex, crop-upscale), anomaly rules, face-embedding FRS (InsightFace/ArcFace + FAISS — phase wiring, seam ready), NAFIS fingerprint correlation, cross-camera trajectory tracking, the pluggable `AnalyticsEngine` ABC. *(HLD §3)*

6. **Watchlist correlation & real-time alerts** *(Area 5)* — CCTNS auto-populates the watchlist (source-tagged, FIR-ref); correlator matches every normalised plate (Redis-cached, sub-ms); on a hit → alert with CCTNS source + VAHAN owner/vehicle + SARTHI DL; dedup window; trajectory stitch across cameras; fan-out to SMS/email/webhook(CCTNS)/FCM. *(HLD §1.3, §11)*

7. **Key technologies, frameworks & tools** *(Area 6)* — FastAPI, React+Leaflet, PostgreSQL+PostGIS, Redis, NATS JetStream, YOLOv8 (Ultralytics), RapidOCR (ONNX Runtime), ffmpeg, OpenAPI + AsyncAPI, ONVIF/GB/T 28181/RTSP, Docker Compose→K8s. Open-source, vendor-neutral.

8. **Scalability** *(Area 7a)* — bandwidth math (320 Gbps raw vs ~1–2 Gbps event plane), gateway pod counts, sharded Postgres, phased rollout 50→2k→10k→80k. *(SCALABILITY.md)*

9. **Interoperability, security & deployment** *(Area 7b)* — adapter registry (vendor-neutral), normalised event schema, GB28181/ONVIF; JWT+dept-scoped RBAC, audit trail, TLS, PII/chain-of-custody; Docker Compose (pilot) → K8s/Helm (state). *(SECURITY.md, ARCHITECTURE_PRINCIPLES.md)*

10. **Live demo (screenshot backup)** — the mandatory test case: 50 heterogeneous cameras, stolen-vehicle trail across 16 cameras on GIS, CCTNS-sourced alert with VAHAN enrichment, fan-out panel. *(in case of venue issues)*

11. **Operational benefits & impact** *(Area 8)* — force multiplication (one operator → effective monitoring of thousands), faster stolen-vehicle recovery, investigation hours saved (plate/camera/time search in minutes not days), interoperability dividend, zero vendor lock-in, avoided ₹400 Cr+ centralisation cost. *(COST_BENEFIT.md)*

12. **What runs today vs roadmap** — honest: ANPR/records/viewing/fan-out/governance/gap-analysis live on sim + real grid; face-embedding, Re-ID, K8s hardening, real gateways on roadmap.

13. **Why us / innovation claim** — deterministic rehearseable demo, hot-swap to government feed, no rip-and-replace, O(events) scaling, pluggable AI/adapters.

14. **Ask & close** — pilot at one district range; contact.

## Demo video script (3 minutes, for the recording)
1. **Login** as admin → dashboard shows live alert feed.
2. **Camera Registry** — 53 cameras, 8 vendors, 5 protocols (incl. GB28181), 26 departments, health/coverage.
3. **Live alert arrives** — stolen-vehicle alert with **CCTNS source + FIR ref + VAHAN owner/vehicle** badge.
4. **Track** → GIS trail builds live across 16 cameras (polyline + pass sequence).
5. **Event Search** by plate → CSV export (the searchable event log).
6. **Records lookup** → plate dossier (VAHAN + CCTNS + SARTHI).
7. **Fan-out panel** → SMS/email/webhook/FCM dispatch log.
8. **Live View / Camera Grid** → real grid cameras playing (HLS + WebRTC toggle).
9. **Gap Analysis** → coverage gaps + ageing report.
10. **Close** — "detect at the edge, correlate at the center; moves events, not video; scales to 80,000."
