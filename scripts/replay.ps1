Write-Host "Replaying scenario playback..." -ForegroundColor Cyan
docker compose restart gateway-sim
Write-Host "Done. The designated vehicle route replays once; alerts fire again for cameras" -ForegroundColor Green
Write-Host "outside the 60s dedup window and the route history extends within the same session." -ForegroundColor Green
