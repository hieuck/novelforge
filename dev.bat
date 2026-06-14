@echo off
cd /d "%~dp0"
echo Starting NovelForge dev environment from %CD%...

REM Try venv Python first, fall back to system Python
if exist "apps\engine\.venv\Scripts\python.exe" (
    "apps\engine\.venv\Scripts\python.exe" scripts/dev.py
) else if exist "apps\engine\.venv\bin\python3" (
    "apps\engine\.venv\bin\python3" scripts/dev.py
) else (
    python scripts/dev.py
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Setup not complete. Run: .\dev.ps1 -Setup
    pause
)
