# Output Report — Government-Provided CCTV Feed (Demo 4)

**Generated:** from the live Trinetra platform · **Source:** government grid cameras (cam01–cam30, cctv.corp8.cloud) · **Analytics:** YOLOv8n vehicle detection + RapidOCR ANPR, edge-processed via the `gateway-ml` ffmpeg-pipe adapter.

This report accompanies the screen-recorded live demonstration. The companion CSV [`OUTPUT_REPORT_GOV_FEED.csv`](OUTPUT_REPORT_GOV_FEED.csv) contains every detected number plate with its UTC timestamp, camera id, vehicle class, and ANPR confidence.

## Methodology
1. **Onboarding** — the grid catalogue was ingested (`scripts/ingest_catalogue.py`), onboarding cam01–cam30 into the registry with authenticated RTSP URLs.
2. **Ingestion** — `gateway-ml` pulls each live RTSP feed over TCP (ffmpeg subprocess, forced TCP, exponential-backoff reconnect, PTS-based timing) and decodes frames at 1280×720.
3. **Analytics** — YOLOv8n detects vehicles (car/motorcycle/bus/truck, conf ≥ 0.45); RapidOCR reads the plate on each vehicle crop (upscaled 1.5–2× for legibility); the Indian-plate regex validates the read.
4. **Correlation** — each normalised plate is matched against the CCTNS-auto-populated watchlist (stolen/wanted/missing/blacklisted); a hit raises a real-time alert with the FIR reference + VAHAN enrichment.
5. **Output** — detections are persisted as events and exported here.

## Detected number plates (live government feed)

| Timestamp (UTC) | Camera | Plate | Vehicle | ANPR conf |
|---|---|---|---|---|
| 2026-09-06T08:28:49 | cam06 | GJ18X3001 | truck | 0.99 |
| 2026-09-06T09:43:25 | cam09 | GJ11S4826 | car | 0.81 |
| 2026-09-07T21:14:10 | cam06 | GI9HZ716 | car | 0.65 |
| 2026-09-07T21:14:14 | cam06 | GJ11BHZ716 | car | 0.76 |
| 2026-09-07T21:36:29 | cam06 | GJ11CH0172 | car | 0.95 |

**Totals:** 5 detections · 5 unique plates · 2 cameras (cam06, cam09) · full detail in `OUTPUT_REPORT_GOV_FEED.csv`.

> Note: the grid operates in a looped-recording mode with ~10 of 30 cameras online at any instant and a per-account concurrent-stream limit; ANPR runs on a curated subset (cam01, cam06) to stay within the limit. Plates are read exactly as the OCR decodes them; normalisation (stripping punctuation) is applied for watchlist matching.
