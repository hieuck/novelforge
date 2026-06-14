param(
    [switch]$Setup
)

$Root = Split-Path -Parent $PSCommandPath
Set-Location $Root

# Optional: run setup first
if ($Setup) {
    Write-Host "=== Installing dependencies ===" -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) { Write-Host "npm install failed" -ForegroundColor Red; exit 1 }

    $venvPy = Join-Path $Root "apps\engine\.venv\Scripts\python.exe"
    if (-not (Test-Path $venvPy)) {
        Write-Host "Creating Python venv..." -ForegroundColor Cyan
        python -m venv apps\engine\.venv
        & $venvPy -m pip install -r apps\engine\requirements.txt
    }
}

Write-Host "=== Starting NovelForge Dev Environment ===" -ForegroundColor Green
Write-Host "  Engine   -> http://127.0.0.1:9000" -ForegroundColor Yellow
Write-Host "  Frontend -> http://127.0.0.1:5173" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Gray

python scripts/dev.py
