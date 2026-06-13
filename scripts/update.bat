@echo off
title NovelForge self-update
setlocal

set BATCH_MODE=0
set REMOTE=https://github.com/hieuck/novelforge.git

if /i "%1"=="batch" set BATCH_MODE=1

echo Fetching the latest code...
git fetch "%REMOTE%"

set FETCH_STATUS=%ERRORLEVEL%
if %FETCH_STATUS% NEQ 0 (
  echo [ERROR] git fetch failed with exit code %FETCH_STATUS%.
  if %BATCH_MODE% EQU 1 exit /b %FETCH_STATUS%
  pause
  exit /b %FETCH_STATUS%
)

for /f "delims= " %%a in ('git rev-parse HEAD') do set LOCAL=%%a
for /f "delims= " %%a in ('git rev-parse FETCH_HEAD') do set REMOTE_COMMIT=%%a

if "%LOCAL%"=="%REMOTE_COMMIT%" (
  echo [UPDATE] Already up to date.
  if %BATCH_MODE% EQU 1 exit /b 0
  pause
  exit /b 0
)

echo Applying update from %LOCAL:~0,7% to %REMOTE_COMMIT:~0,7%...
git reset --hard "%REMOTE_COMMIT%"

set RESET_STATUS=%ERRORLEVEL%
if %RESET_STATUS% NEQ 0 (
  echo [ERROR] git reset --hard failed with exit code %RESET_STATUS%.
  if %BATCH_MODE% EQU 1 exit /b %RESET_STATUS%
  pause
  exit /b %RESET_STATUS%
)

echo Reinstalling dependencies...
call npm install

set INSTALL_STATUS=%ERRORLEVEL%
if %INSTALL_STATUS% NEQ 0 (
  echo [ERROR] npm install failed with exit code %INSTALL_STATUS%.
  if %BATCH_MODE% EQU 1 exit /b %INSTALL_STATUS%
  pause
  exit /b %INSTALL_STATUS%
)

echo [UPDATE] Done. Restart NovelForge to continue.
if %BATCH_MODE% EQU 1 exit /b 0
pause
