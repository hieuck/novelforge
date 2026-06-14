@echo off
cd /d "%~dp0.."
echo Starting NovelForge dev environment from %CD%...
python scripts\dev.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to start. Check that Python venv is set up.
    echo Run: python -m venv apps\engine\.venv
    echo Then: apps\engine\.venv\Scripts\pip install -r apps\engine\requirements.txt
    pause
)
