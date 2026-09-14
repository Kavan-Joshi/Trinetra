param(
    [double]$Speed = 20,
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"
$env:TRINETRA_SIM_SPEED = "$Speed"

Write-Host "== Trinetra demo bring-up (sim speed x$Speed) ==" -ForegroundColor Cyan
$ErrorActionPreference = "Continue"
docker compose down -v 2>&1 | Out-Null
$ErrorActionPreference = "Stop"

if (-not $NoBuild) { docker compose build }

docker compose up -d postgres redis nats core-api frontend

Write-Host "Waiting for core API..." -ForegroundColor Yellow
$ok = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $ok) { Write-Host "Core API did not become healthy. Check: docker compose ps / docker compose logs core-api" -ForegroundColor Red; exit 1 }

Write-Host "Seeding registry + watchlist..." -ForegroundColor Yellow
docker compose run --rm seeder

Write-Host "Starting correlator, records (CCTNS sync), notifier, streamer and janitor..." -ForegroundColor Yellow
docker compose up -d correlator records notifier streamer janitor
Start-Sleep -Seconds 6

Write-Host "Starting event gateway..." -ForegroundColor Yellow
docker compose up -d gateway-sim

Write-Host ""
Write-Host "== DEMO READY ==" -ForegroundColor Green
Write-Host "Dashboard : http://localhost:8080   (login: admin / admin123)"
Write-Host "API docs  : http://localhost:8000/docs"
Write-Host ""
Write-Host "Test case runbook: the stolen Creta (GJ-01-KA-1234) starts passing cameras ~15s after"
Write-Host "the gateway starts. Watch live alerts, open one, click 'Track' for the GIS trail."
Write-Host "Full scripted route completes in ~$([math]::Round(1500 / $Speed)) seconds."
Write-Host ""
Start-Process "http://localhost:8080"
