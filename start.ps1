# VADP PowerShell Localhost Starter Script
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "          VADP Zero-Trust Legal AI Platform            " -ForegroundColor Yellow
Write-Host "            Launching Localhost Services (PS)              " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$RootDir = $PSScriptRoot

Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RootDir\backend'; python -m uvicorn app.main:app --reload --port 8000"

Start-Sleep -Seconds 3

Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RootDir\frontend'; npm run dev"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  SUCCESS! Localhost services started in separate windows:" -ForegroundColor Yellow
Write-Host "    - Frontend Portal:      http://localhost:3000" -ForegroundColor White
Write-Host "    - Backend REST API:     http://localhost:8000" -ForegroundColor White
Write-Host "    - API Interactive Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
