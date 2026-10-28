<#
.SYNOPSIS
    TrueRoll helper script for Windows PowerShell.
    Usage: .\run.ps1 <command>

.EXAMPLE
    .\run.ps1 seed
    .\run.ps1 run-backend
    .\run.ps1 run-frontend
    .\run.ps1 test
    .\run.ps1 reset-demo
    .\run.ps1 evaluate
#>

param([string]$Command = "help")

$BackendDir = Join-Path $PSScriptRoot "backend"
$FrontendDir = Join-Path $PSScriptRoot "frontend"

switch ($Command) {

    "seed" {
        Write-Host "Seeding database..." -ForegroundColor Cyan
        Set-Location $BackendDir
        python -m scripts.init_db
    }

    "reset-demo" {
        Write-Host "Resetting demo (drops and reseeds)..." -ForegroundColor Yellow
        Set-Location $BackendDir
        python -m scripts.init_db --reset
    }

    "run-backend" {
        Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Green
        Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Gray
        Set-Location $BackendDir
        uvicorn app.main:app --reload --port 8000
    }

    "run-frontend" {
        Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Green
        Set-Location $FrontendDir
        npm run dev
    }

    "test" {
        Write-Host "Running backend tests..." -ForegroundColor Cyan
        Set-Location $BackendDir
        python -m pytest tests/ -v
    }

    "test-fast" {
        Write-Host "Running backend tests (stop on first fail)..." -ForegroundColor Cyan
        Set-Location $BackendDir
        python -m pytest tests/ -v -x
    }

    "evaluate" {
        Write-Host "Running evaluation suite..." -ForegroundColor Cyan
        Set-Location $BackendDir
        python -m scripts.evaluate_anomaly
        python -m scripts.evaluate
    }

    "e2e" {
        Write-Host "Running Playwright e2e tests (backend + frontend must already be running)..." -ForegroundColor Cyan
        Set-Location $FrontendDir
        npx playwright test e2e/demo-script.spec.ts
    }

    "install" {
        Write-Host "Installing all dependencies..." -ForegroundColor Cyan
        Set-Location $BackendDir
        pip install -r requirements.txt
        Set-Location $FrontendDir
        npm install
        Write-Host "Done. Run .\run.ps1 seed next." -ForegroundColor Green
    }

    default {
        Write-Host ""
        Write-Host "TrueRoll -- available commands:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  .\run.ps1 install        Install Python + Node dependencies"
        Write-Host "  .\run.ps1 seed           Create database and load demo data"
        Write-Host "  .\run.ps1 reset-demo     Drop everything and reseed from scratch"
        Write-Host "  .\run.ps1 run-backend    Start FastAPI server on :8000"
        Write-Host "  .\run.ps1 run-frontend   Start Vite dev server on :5173"
        Write-Host "  .\run.ps1 test           Run 71 backend tests"
        Write-Host "  .\run.ps1 evaluate       Run evaluation suite"
        Write-Host "  .\run.ps1 e2e            Run Playwright demo tests"
        Write-Host ""
        Write-Host "Quick start:" -ForegroundColor Yellow
        Write-Host "  1. .\run.ps1 install"
        Write-Host "  2. copy .env.example .env"
        Write-Host "  3. .\run.ps1 seed"
        Write-Host "  4. .\run.ps1 run-backend    (keep open)"
        Write-Host "  5. .\run.ps1 run-frontend   (new terminal, keep open)"
        Write-Host "  6. Open http://localhost:5173 in your browser"
        Write-Host ""
    }
}
