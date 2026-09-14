# Trinetra — Deployment Guide (New Laptop)

Run the full Trinetra platform on a different machine in ~30 minutes.

## Prerequisites

1. **Docker Desktop** — download from https://docker.com, install, start it. Ensure WSL2 is enabled.
2. **The repo** — copy the entire `sentinel-gujarat` folder to the new laptop (USB, cloud, or git).
3. **Internet** — needed for Docker image builds + grid RTSP + model downloads.

## Step-by-step

### 1. Copy the repo
Copy the `sentinel-gujarat` folder to the new laptop, e.g. `C:\Projects\sentinel-gujarat`.

### 2. Create the `.env` file
In the repo root, copy `.env.example` to `.env` and verify the grid credentials:
```ini
TRINETRA_GRID_EMAIL=kavanjoshi890@gmail.com
TRINETRA_GRID_PASSWORD=9WXY-ST7Y-C5E9
TRINETRA_STREAMER_MODE=live
TRINETRA_SEED_SIM_CAMERAS=false
TRINETRA_FACE_DETECTION=true
```

### 3. Start the base stack
Open PowerShell in the repo folder:
```powershell
docker compose up -d
```
This starts: PostgreSQL+PostGIS, Redis, NATS, core-api, correlator, records, notifier, streamer, janitor, frontend.

Wait for the API to be healthy:
```powershell
# wait ~30s, then:
curl http://localhost:8000/health
# should return: {"status":"ok","service":"core-api"}
```

### 4. Seed the database (departments + users + watchlist)
```powershell
docker compose run --rm seeder
```
Expected: `Seed complete: 28 departments, 0 new cameras, ...`

### 5. Onboard the real grid cameras (cam01–cam30)
```powershell
docker compose --profile grid run --rm ingester
```
Expected: `ingest complete: 30 created, 0 updated`

### 6. Start the AI analytics gateway (ANPR + face detection)
```powershell
docker compose --profile ml up -d --build gateway-ml
```
**This takes 10–15 minutes the first time** (downloads torch, ultralytics, opencv, rapidocr, insightface + ffmpeg). Subsequent starts are instant (cached).

The gateway-ml will:
- Pull all 30 grid RTSP feeds (2fps, TCP).
- Run YOLOv8n vehicle detection + RapidOCR ANPR + InsightFace face detection on each.
- Publish detection events to the correlator → alerts → console.

### 7. Verify
- **Operator console:** http://localhost:8082 (login: `admin / admin123`)
- **API docs:** http://localhost:8000/docs
- **Camera grid:** http://localhost:8082/#/grid
- **Live view:** http://localhost:8082/#/live

### 8. (Optional) Enroll a face for recognition
```powershell
$token = (Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body @{username="admin";password="admin123"}).access_token
curl -X POST http://localhost:8000/api/v1/faces/enroll -H "Authorization: Bearer $token" -F "name=Suspect Name" -F "category=wanted_person" -F "file=@photo.jpg"
```

## Quick reference — all commands
```powershell
# full bring-up (from scratch)
docker compose up -d
docker compose run --rm seeder
docker compose --profile grid run --rm ingester
docker compose --profile ml up -d --build gateway-ml

# stop everything
docker compose down

# stop + wipe data (fresh start)
docker compose down -v
```

## Troubleshooting
| Issue | Fix |
|---|---|
| Port 8082 busy | Edit `docker-compose.yml` → `frontend.ports` → change `8082:80` to another port |
| gateway-ml build hangs | Cancel + retry; or build without `--build` if image already exists |
| No cameras in grid | Check `.env` credentials; re-run `docker compose --profile grid run --rm ingester` |
| 401 on RTSP | Grid may be in restricted mode; wait + retry, or verify credentials at cctv.corp8.cloud |
| High CPU | Normal with 30 cameras; reduce by setting `TRINETRA_FACE_DETECTION=false` in `.env` |
| Docker Desktop 500 errors | Restart Docker Desktop + run `wsl --shutdown` |

## What's included
- 30 real grid cameras (cam01–cam30) across 5 departments
- ANPR (YOLOv8n + RapidOCR) on all cameras
- Face detection (InsightFace ArcFace) on all cameras
- CCTNS auto-watchlist + VAHAN/SARTHI/NAFIS enrichment
- Real-time alerts + fan-out (SMS/email/webhook/FCM)
- Live viewing (HLS + WebRTC) + camera grid mosaic
- Gap analysis, department governance, retention
