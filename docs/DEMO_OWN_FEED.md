# Demo 3 — Demonstration on Participant's Own Feed (screen-record, 2–3 min)

The platform's own simulated estate — a fully operational backend (not a mock-up): a 50-camera heterogeneous corridor (8 vendors, 6 VMS, 5 protocols), a scripted stolen-vehicle scenario, CCTNS-auto-populated watchlist, VAHAN enrichment, real-time alerts, GIS trajectory, and fan-out. Record this with any screen recorder (OBS / Win+G / QuickTime).

## Bring-up
```powershell
.\scripts\demo.ps1     # full stack on http://localhost:8082 (login: admin / admin123)
```
The stolen black Creta **GJ-01-KA-1234** begins moving ~15 s after the gateway starts; its 16-camera trail completes in ~75 s at 20× playback.

## Recording script (≈2.5 min)
1. **(0:00)** Login → **Dashboard**: live alert feed streaming; stat cards (cameras online, events 24h, active alerts, watchlist).
2. **(0:10)** **Camera Registry**: 50 cameras, 8 vendors, 5 protocols (point at GB28181 rows), 26 departments, health/coverage badges.
3. **(0:25)** A **STOLEN VEHICLE** alert arrives (live) — open it: evidence frame, **Source: CCTNS · FIR/1246/2026/VASTRAPUR** badge, **VAHAN: Rakesh J. Mehta · Hyundai Creta · insurance valid**.
4. **(0:45)** Click **Track** → **Live Map**: blue polyline builds live across 16 cameras (Nehru Bridge → Sachivalaya Gate), numbered pass sequence, red alert pins.
5. **(1:15)** **Event Search**: filter by plate `GJ-01-KA` → all 16 passes with frames + timestamps → **CSV export** (the searchable event log / output artefact).
6. **(1:35)** **Records**: plate `GJ-01-KA-1234` → dossier (VAHAN + CCTNS stolen + SARTHI DL). Person lookup `Rahil Shaikh` → CCTNS wanted + NAFIS 92% fingerprint match.
7. **(1:55)** **Fan-out**: the alert dispatched to SMS / email / webhook(CCTNS) / FCM with status + timestamps.
8. **(2:10)** **Gap Analysis**: per-zone coverage gaps + ageing infrastructure + recommendations → **Download report (CSV)**.
9. **(2:25)** Close: *"detect at the edge, correlate at the center — moves events, not video; the watchlist is auto-populated from CCTNS, every alert is enriched, face recognition works, and it scales to 80,000 cameras."*

## What this proves (maps to Demo-3 criteria)
- ✅ Onboarding & processing of live/recorded CCTV feeds (50-camera sim + real RTSP path)
- ✅ AI-powered detection & analytics (YOLOv8n + RapidOCR ANPR + InsightFace face detection + anomaly)
- ✅ Correlation with a watchlist (CCTNS-sourced stolen/wanted/missing/blacklisted)
- ✅ Automatic real-time alerts + visualisation on match (dashboard, map, fan-out)
- ✅ Face recognition: enroll a face → detected on camera → accurate cosine-similarity match → wanted-person alert
- ✅ Fully functional operational backend (no mock-ups)

> For Demo 4 (government feed), see [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) §3 + [`OUTPUT_REPORT_GOV_FEED.md`](OUTPUT_REPORT_GOV_FEED.md).
