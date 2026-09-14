# Trinetra — Submission Package

**Gujarat Police Innovation Challenge 2026 — Integrated CCTV / Video Management & Analytics Platform**

## What to submit (and where it lives)

| # | Required deliverable | File / location |
|---|---|---|
| 1 | **Solution Presentation (PPT/PDF)** | [`docs/PRESENTATION_OUTLINE.md`](PRESENTATION_OUTLINE.md) — 14-slide outline mapping all 8 content areas + a 3-min demo-video script. Render to PDF/PPT for submission. |
| 2 | **Technical Proposal — HLD** | [`docs/HLD.md`](HLD.md) — covers all 9 required areas (architecture, heterogeneous integration, ingestion, watchlist correlation, AI analytics incl. ANPR/FRS/tracking, alert workflow + prioritisation, scalability/interop/security for 80k, technical prerequisites & info required from departments). |
| 3 | **Demo on own feed (screen recording, 2–3 min)** | [`docs/DEMO_OWN_FEED.md`](DEMO_OWN_FEED.md) — runbook for the recording. Bring-up: `.\scripts\demo.ps1`. |
| 4 | **Live demo on govt feed (screen recording + output report)** | [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md) §3 (gov-feed onboarding) · output report: [`docs/OUTPUT_REPORT_GOV_FEED.csv`](OUTPUT_REPORT_GOV_FEED.csv) + [`docs/OUTPUT_REPORT_GOV_FEED.md`](OUTPUT_REPORT_GOV_FEED.md) (detected plates + timestamps). |

## Supporting documents
- [`docs/DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) — step-by-step deploy on a new laptop (`scripts\deploy.ps1`)
- [`docs/DEPLOYMENT_AND_OPERATIONS.md`](DEPLOYMENT_AND_OPERATIONS.md) — the 7 operational areas (central/regional/edge compute, GPU, bandwidth + low-bandwidth, hot/warm/cold storage, load-balancing/scaling/monitoring, HA/DR/cybersecurity, costs)
- [`docs/INTEGRATION.md`](INTEGRATION.md) — records/GB28181/community/viewing integration
- [`docs/ARCHITECTURE_PRINCIPLES.md`](ARCHITECTURE_PRINCIPLES.md) — RFP architecture-principles compliance
- [`docs/SCALABILITY.md`](SCALABILITY.md) · [`docs/SECURITY.md`](SECURITY.md) · [`docs/COST_BENEFIT.md`](COST_BENEFIT.md)
- [`docs/SAMPLE_GAP_ANALYSIS_REPORT.md`](SAMPLE_GAP_ANALYSIS_REPORT.md) — Model-1 sample report
- [`docs/GRID_FEEDS.md`](GRID_FEEDS.md) — government-feed integration
- [`docs/asyncapi.yaml`](asyncapi.yaml) — event-bus contract (AsyncAPI)
- [`README.md`](../README.md) — runbook + service map

## Hosted platform (for the screening committee)
- **URL:** http://localhost:8082 (when running locally) — or deploy to a host and share the URL
- **Test logins:** `admin / admin123` · `operator / operator123` · `analyst / analyst123` · `traffic / traffic123` (dept-scoped) · `rto / rto123` · `fcs / fcs123`
- **API docs:** http://localhost:8000/docs (OpenAPI)
- **Bring-up:** `.\scripts\demo.ps1` (sim) · government feed: set `TRINETRA_GRID_EMAIL`/`TRINETRA_GRID_PASSWORD` in `.env`, then `docker compose --profile grid run --rm ingester` + `docker compose --profile ml up -d gateway-ml`

## Source code (GitHub/GitLab)
- Repo root: services (`gateway`, `correlator`, `core_api`, `records`, `notifier`, `streamer`, `janitor`), `packages/trinetra_core`, `frontend`, `sim`, `scripts`, `tests`, `docs`
- `docker-compose.yml` (13 services) · `tests/` (33 unit tests) · `docs/` (11 docs)
- Verify: `python -m pytest tests -q` · `python -m compileall packages services sim scripts` · `npx tsc --noEmit` (in `frontend/`)

## Submission method (per RFP)
- Unlisted YouTube link (the two screen recordings)
- Google Drive / OneDrive link (anyone-with-link viewer) for the recordings + output report + PDFs
- Optionally the hosted URL + test credentials above
- Optionally the GitHub/GitLab repo link

## Recording checklist
- [ ] Demo 3 (own feed): follow `DEMO_OWN_FEED.md`, 2–3 min, 1080p
- [ ] Demo 4 (gov feed): onboard grid (`ingester`), show live viewing + ANPR, attach `OUTPUT_REPORT_GOV_FEED.csv`
- [ ] Render `PRESENTATION_OUTLINE.md` to PDF
- [ ] Upload recordings as unlisted YouTube + Drive; share URLs
