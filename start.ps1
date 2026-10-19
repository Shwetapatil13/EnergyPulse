# EnergyPulse — Start All Services
# Run this script from the project root: .\start.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  EnergyPulse — Starting Services" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# 1. Start Backend (FastAPI on port 8000)
Write-Host "`n[1/2] Starting Backend (FastAPI) on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python -m backend.app.main" -WorkingDirectory $PSScriptRoot

Start-Sleep -Seconds 3

# 2. Start Frontend (Vite dev server on port 5173)
Write-Host "[2/2] Starting Frontend (Vite) on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WorkingDirectory "$PSScriptRoot\frontend"

Write-Host "`n✅ Both services launched in separate windows." -ForegroundColor Green
Write-Host "   Backend : http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`nPress Ctrl+C in each window to stop." -ForegroundColor DarkGray
