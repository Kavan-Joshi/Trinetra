# Trinetra — one-command deployment on a new laptop
# Usage:  .\scripts\deploy.ps1
# Prerequisites: Docker Desktop running, .env file configured with grid credentials

param(
    [switch]$SkipIngest  # skip the grid ingester (use sim cameras instead)
)

$ErrorActionPreference = "Stop"
Write-Host "== Trinetra Deployment ==" -ForegroundColor Cyan

# 1. Check .env
if (-not (Test-Path .env)) {
    Write-Host "ERROR: .env file not found. Copy .env.example to .env and fill in grid credentials." -ForegroundColor Red
    exit 1
}

# 2. Build + start base stack
Write-Host "`n[1/5] Starting base stack (Postgres, Redis, NATS, API, frontend)..." -ForegroundColor Yellow
docker compose up -d --build
if (-not $?) { Write-Host "Failed to start base stack" -ForegroundColor Red; exit 1 }

# 3. Wait for API health
Write-Host "`n[2/5] Waiting for core API..." -ForegroundColor Yellow
$ok = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $ok) { Write-Host "Core API did not become healthy" -ForegroundColor Red; exit 1 }
Write-Host "  API healthy ✓" -ForegroundColor Green

# 4. Seed database
Write-Host "`n[3/5] Seeding database (28 departments, users, watchlist)..." -ForegroundColor Yellow
docker compose run --rm seeder

# 5. Ingest grid cameras (if not skipped)
if (-not $SkipIngest) {
    Write-Host "`n[4/5] Onboarding 30 grid cameras from cctv.corp8.cloud..." -ForegroundColor Yellow
    docker compose --profile grid run --rm ingester
} else {
    Write-Host "`n[4/5] Skipping grid ingest (sim mode)" -ForegroundColor DarkGray
}

# 6. Start AI gateway
Write-Host "`n[5/5] Starting AI gateway (ANPR + face detection)..." -ForegroundColor Yellow
Write-Host "  First build takes 10-15 min (downloads torch, ultralytics, insightface)..." -ForegroundColor DarkGray
docker compose --profile ml up -d --build gateway-ml

# Done
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Console:  http://localhost:8082"
Write-Host "  API:      http://localhost:8000/docs"
Write-Host "  Login:    admin / admin123"
Write-Host ""
Write-Host "  The AI gateway is building/starting."
Write-Host "  ANPR events will appear in 2-5 minutes."
Write-Host "========================================" -ForegroundColor Green
