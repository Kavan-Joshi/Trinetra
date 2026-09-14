# Trinetra — External Live Camera Grid Integration

How Trinetra consumes the provided live CCTV feed grid (the real camera infrastructure). The grid publishes each camera over three transports; Trinetra pulls RTSP for analytics and re-emits HLS for operators, following the grid's published consumption contract.

## 1. Grid access model (as provided)

| Protocol | Endpoint | Trinetra use |
|---|---|---|
| HLS | `https://cctv.corp8.cloud/<id>/index.m3u8` (CDN, password) | Available; Trinetra re-emits its own HLS from RTSP so operators auth via JWT, not the grid password. |
| RTSP | `rtsp://<email%40>:<password>@103.250.160.189:8554/stream/<id>` | **Primary ingestion** — the gateway pulls this for AI/ANPR analytics. |
| WebRTC (WHEP) | `http://<email%40>:<password>@103.250.160.189:8889/stream/<id>/whep` | Low-latency preview; the streamer's WHIP/WHEP path is available alongside. |

- `<id>` is `cam01 … cam30`. The camera set is read from the catalogue, never hard-coded.
- The `@` in the access email is percent-encoded as `%40` when embedded in the URL userinfo.
- Only emails on the grid's approved access list can connect.

## 2. Configuration (credentials via environment only — never committed)

```ini
TRINETRA_GRID_EMAIL=you@example.com
TRINETRA_GRID_PASSWORD=your-access-password
TRINETRA_GRID_CATALOGUE_URL=https://cctv.corp8.cloud/cameras.json
TRINETRA_GRID_RTSP_HOST=103.250.160.189:8554
TRINETRA_GRID_HLS_BASE=https://cctv.corp8.cloud
TRINETRA_GRID_WHEP_HOST=103.250.160.189:8889
```

Set these in `.env` (see `.env.example`). Leave blank to run the simulator.

## 3. Onboarding the grid into the registry

The ingester fetches `cameras.json` (HTTP basic auth with the email + password), normalises the payload, constructs the three URLs per camera, and upserts them into the camera registry (`protocol=rtsp`, `stream_url` = the RTSP URL the gateway/streamer pull):

```powershell
# put the credentials in .env first, then:
docker compose --profile grid run --rm ingester
```

`scripts/ingest_catalogue.py` is idempotent (re-running updates stream URLs / metadata). The grid cameras then appear in the registry, on the GIS map, and in Live View alongside the simulated estate.

## 4. Running analytics on the real grid

The gateway's **live mode** reads cameras from the registry DB (so it sees the ingested grid cameras) and pulls each RTSP stream through the hardened `RTSPAdapter`:

```powershell
docker compose --profile gpu up -d --build gateway-ml      # YOLOv8n + RapidOCR on live RTSP
```

`gateway-ml` runs `TRINETRA_GATEWAY_MODE=rtsp`; detections/events/alerts flow through the same correlator → records → notifier → console pipeline as the simulator. Switch back to the simulator any time with `gateway-sim`.

### RTSPAdapter — compliance with the grid consumption contract

The adapter implements every "do" and avoids every "don't":

- **Force RTSP over TCP** — `OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp` is set process-wide; opens use `cv2.CAP_FFMPEG`. (UDP across NAT/firewalls corrupts frames.)
- **Reconnect with exponential backoff** — 2 s → 4 s → 8 s … capped at 30 s; never a tight loop. Backoff resets on the first good frame.
- **Tolerate inter-frame gaps** — a failed `read()` does **not** reconnect; only after `READ_FAIL_THRESHOLD` (8) consecutive failures is the stream treated as lost. Inter-frame gaps are normal.
- **Drive timing from PTS, not arrival/FPS** — `CAP_PROP_POS_MSEC` is captured per frame and stored on the event (`attributes.pts_ms`); detection cadence is time-based, independent of `CAP_PROP_FPS`.
- **Scene-discontinuity (loop-point) recovery** — a backward PTS jump is logged as a loop cut and the adapter continues (state is per-frame; no crash, no reconnect).
- **Decoder join warnings are non-fatal** — exceptions in inference are logged and the loop continues.
- **Pace the load** — one capture per camera; detection cadence limits CPU; idle captures are not opened.
- **Email `%40`-encoded** — the ingester encodes the userinfo, so the adapter uses the `stream_url` verbatim.

## 5. Live operator viewing of the real grid

The `streamer` (live mode) pulls each grid RTSP stream over TCP and re-emits HLS for the console; operators open **Live View → Watch** on any grid camera. The streamer resolves cameras from the registry DB, so grid cameras appear automatically after ingestion.

```powershell
$env:TRINETRA_STREAMER_MODE="live"; docker compose up -d --build streamer
```

For sub-second preview, build the streamer with `INSTALL_WEBRTC=true` and toggle to WebRTC in Live View.

## 6. Pre-submission checklist (mapped)

| Grid requirement | Trinetra |
|---|---|
| RTSP clients force TCP; remote clients use HLS | ✅ `rtsp_transport;tcp` env; streamer serves HLS |
| No timing logic depends on `CAP_PROP_FPS` or arrival time | ✅ PTS-based; monotonic cadence only |
| Inter-frame gaps do not crash/stall the pipeline | ✅ threshold-gated reconnect |
| Reconnect with backoff implemented and tested | ✅ 2 s → 30 s cap |
| Decoder join warnings logged, not fatal | ✅ try/except + continue |
| Camera list read from `cameras.json`; mixed H.264/H.265 handled | ✅ ingester reads catalogue; ffmpeg auto-detects codec |
| Sane across a scene discontinuity (loop point) | ✅ PTS-jump detection, continue |
