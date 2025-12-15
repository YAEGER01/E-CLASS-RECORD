# E-Class Record System Startup Script (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " E-Class Record System Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Green
& .venv\Scripts\Activate.ps1

# Check if dependencies are installed
Write-Host "[INFO] Checking dependencies..." -ForegroundColor Green
python -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Flask not found. Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "[INFO] Starting Flask application..." -ForegroundColor Green
Write-Host "[INFO] Access the application at: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start the application
python app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Application exited with an error" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
