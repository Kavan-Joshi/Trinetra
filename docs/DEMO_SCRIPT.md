# Trinetra — Demo Runbook (Mandatory Test Case)

## 1. Pre-flight (night before + morning of)

```powershell
cd C:\Projects\sentinel-gujarat
.\scripts\demo.ps1            # full fresh bring-up; browser opens automatically
```

- Confirm: dashboard stats show **47/50 cameras online**, watchlist shows 5 entries.
- Keep a phone hotspot ready as network fallback (map tiles need internet; the rest of the stack is fully local).
- Optional: `.\scripts\demo.ps1 -Speed 10` for a slower, more narratable vehicle movement.

## 2. The judge-run test case (≈4 minutes)

| # | Requirement from problem statement | What you show | Where |
|---|---|---|---|
| 1 | ~50 heterogeneous cameras onboarded | Camera Registry: 50 cams, 8 vendors (Hikvision, CP Plus, Dahua, Axis, Bosch, Pelco, Honeywell, Vivotek), 6 VMS platforms, 4 protocols — plus 3 offline cams proving live status | Cameras page |
| 2 | Live feeds integrated | Gateway adapters streaming events in real time (point at `docker compose logs -f gateway-sim correlator` in a side terminal) | Terminal |
| 3 | Real-time alerts (timestamp + location) | The stolen black Creta **GJ-01-KA-1234** triggers a STOLEN VEHICLE alert ~15 s after gateway start; blacklisted Swift GJ-05-AB-4321 and stolen Activa fire later; anomaly alerts (crowd, unattended object) demonstrate analytics breadth | Dashboard live feed |
| 4 | Route/movement history | Click **Track** on the Creta alert → ordered trail across **16 cameras** from Nehru Bridge to Sachivalaya Gate, first/last seen timestamps, pass counter | Live Map |
| 5 | GIS visualization | Blue polyline with numbered pass sequence over camera markers + red alert pins; "Live-follow" extends the trail automatically as the vehicle progresses | Live Map |
| 6 | Searchable event log | Event Search: filter by plate `GJ-01-KA` → all 16 passes with frames; filter by camera/time range; **CSV export** hands judges the output-report artefact | Event Search |
| 7 | Government DB integration | Watchlist rows show **Source: CCTNS · FIR/1246/2026** (auto-synced, not manual); the Creta alert card carries **VAHAN: owner · Hyundai Creta · insurance status**; Records page → plate `GJ-01-KA-1234` returns the full dossier (VAHAN + CCTNS + SARTHI) | Watchlist / Alerts / Records |
| 8 | Live viewing | Cameras → **Watch** on any camera → Live View plays a live HLS feed (test pattern + camera name + clock); toggle to **WebRTC** (sub-second) if built with `INSTALL_WEBRTC=true` | Live View |
| 9 | Real-time alert fan-out | Fan-out panel shows each alert dispatched to SMS / email / webhook(CCTNS) / FCM with status + timestamp; the webhook receipt is logged end-to-end | Fan-out |
| 10 | Department governance | Log out → log in as **traffic / traffic123** → Cameras/Alerts scoped to Traffic dept only; Departments page shows 26 depts with editable per-dept retention + dry-run report | Login / Cameras / Departments |
| 11 | Community cameras | Community page → onboard a private camera with consent → it appears in the registry tagged `community` and is viewable in Live View | Community / Cameras |
| 12 | Model 1: registry & gap analysis | Cameras → filter by **health/maintenance** + **Export CSV**; Live Map → toggle **coverage footprints**; Gap Analysis → per-zone coverage gaps (Zone-4/5 flagged), ageing buckets (20 cameras >7y), EOL firmware (17), recommendations + **Download report (CSV)** | Cameras / Live Map / Gap Analysis |
| 13 | Face detection & recognition | Enroll a face via `POST /api/v1/faces/enroll` (upload photo) → when that face appears on any camera → InsightFace ArcFace embedding match (cosine ≥ 0.38) → **WANTED PERSON DETECTED (face match)** alert with the enrolled name + match score | Records / Alerts |

**Narrative spine (say this):** "Fifty cameras, eight vendors, five protocols including GB/T 28181, six VMS platforms — the gateway adapters federate them into one event stream. Detection happens at the edge; only kilobytes cross the network. The watchlist is auto-populated from CCTNS, so every stolen-vehicle alert carries the FIR reference and VAHAN owner details. Face recognition uses InsightFace ArcFace embeddings — enroll a face, and when it appears on any camera, the correlator matches it via cosine similarity and raises a wanted-person alert. The correlator stitches the trail camera-to-camera, fans the alert to SMS/email/CCTNS-webhook/mobile, and pushes it to operators in real time. Operators can also pull a live view on demand. This architecture scales to 80,000 cameras because it moves events, not video."

## 3. Switching to the provided live camera grid

The real feed grid publishes each camera as RTSP/HLS/WebRTC. Trinetra ingests the grid catalogue and pulls RTSP (TCP) for analytics. Full procedure in [`docs/GRID_FEEDS.md`](GRID_FEEDS.md).

1. Put your grid credentials in `.env` (see `.env.example`):
   ```ini
   TRINETRA_GRID_EMAIL=you@example.com
   TRINETRA_GRID_PASSWORD=your-access-password
   ```
2. Ingest the grid catalogue into the registry (idempotent):
   ```powershell
   docker compose --profile grid run --rm ingester
   ```
   The grid cameras (`cam01…cam30`) now appear in the registry, on the GIS map, and in Live View.
3. Start the live inference gateway (pulls RTSP over TCP, runs YOLOv8n + RapidOCR):
   ```powershell
   docker compose --profile gpu up -d --build gateway-ml
   ```
   The same correlator → records → notifier → console pipeline works unchanged on real video.
4. (Optional) Live operator viewing from the real grid:
   ```powershell
   $env:TRINETRA_STREAMER_MODE="live"; docker compose up -d --build streamer
   ```
   Open **Live View → Watch** on any grid camera.
5. **Fallback if the live feed can't be opened on stage:** stop `gateway-ml`, restart `gateway-sim` — the scripted scenario runs identically. The RTSP adapter, ingestion, and pipeline are the same code path the live grid uses.

## 4. Failure-mode playbook

| Symptom | Fix |
|---|---|
| Dashboard empty / login fails | `docker compose ps` → is core-api healthy? `docker compose logs core-api` |
| No alerts arriving | `docker compose logs correlator gateway-sim` — gateway logs each adapter's event count every 50 events |
| Map tiles blank (no internet) | Everything except basemap tiles is local; switch on phone hotspot or narrate over the trail markers (trail/alerts still render) |
| Want to re-run the scenario | `.\scripts\replay.ps1` (new tracking session; events accumulate) or full reset `.\scripts\demo.ps1` |
| Port 8000/8080 busy | Edit ports in `docker-compose.yml` |

## 5. Evidence pack for submission

- Screen-record: login → live alert → track trail → event search + CSV export (~3 min, 1080p).
- Export of the event log CSV and alerts table screenshot (output report).
- This runbook + HLD + architecture diagram in the PPT.
