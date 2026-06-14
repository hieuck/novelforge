param(
    [string]$AgentRoot,
    [string]$VenvRoot,
    [string]$Branch = "main",
    [string]$DesktopStampPath,
    [string]$LogFile,
    [string]$ExePath
)

$ErrorActionPreference = "Stop"
$LogPath = if ($LogFile) { $LogFile } else { Join-Path $env:LOCALAPPDATA "novelforge\logs\update.log" }

function Write-Log { param([string]$Msg) $Msg | Out-File -FilePath $LogPath -Append -Encoding utf8 }

function Compute-ContentHash {
    param([string]$Dir)
    $hash = [System.Security.Cryptography.SHA256]::Create()
    try {
        $files = & "git" "ls-files" 2>&1 | Where-Object { $_ -and $_ -notlike "fatal*" }
        if (-not $files) { return $null }
        foreach ($f in $files) {
            $fullPath = Join-Path $Dir $f
            if (Test-Path $fullPath) {
                $content = [System.IO.File]::ReadAllBytes($fullPath)
                $hash.TransformBlock($content, 0, $content.Length, $null, 0) | Out-Null
            }
        }
        $hash.TransformFinalBlock(@(), 0, 0) | Out-Null
        return [BitConverter]::ToString($hash.Hash).Replace("-", "").ToLower()
    } finally { $hash.Dispose() }
}

Write-Log "=== Update started at $(Get-Date -Format o) ==="
Write-Log "AgentRoot: $AgentRoot | Branch: $Branch"

# Step 1: Wait for lock release
$timeout = 20
$elapsed = 0
while ($elapsed -lt $timeout) {
    $locked = $false
    try {
        $testFile = Join-Path $AgentRoot ".git\HEAD"
        if (Test-Path $testFile) {
            $stream = [System.IO.File]::Open($testFile, 'Open', 'Read', 'None')
            $stream.Close()
        }
    } catch {
        $locked = $true
    }
    if (-not $locked) { break }
    Start-Sleep -Seconds 1
    $elapsed++
}
if ($elapsed -ge $timeout) {
    Write-Log "Timeout waiting for lock release, force-killing NovelForge.exe"
    Get-Process "NovelForge" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Step 2: Git pull
Set-Location $AgentRoot
Write-Log "Fetching origin $Branch..."
& "git" fetch origin $Branch 2>&1 | ForEach-Object { Write-Log $_ }
if ($LASTEXITCODE -ne 0) {
    Write-Log "git fetch failed (exit $LASTEXITCODE)"
    exit 1
}
$hasDirty = & "git" status --porcelain
if ($hasDirty) {
    Write-Log "Stashing dirty changes..."
    & "git" stash push --include-untracked -m "auto-stash before update" 2>&1 | ForEach-Object { Write-Log $_ }
    if ($LASTEXITCODE -ne 0) {
        Write-Log "git stash failed (exit $LASTEXITCODE)"
        exit 1
    }
}
$prevHead = & "git" "rev-parse" "HEAD"
Write-Log "Pulling $Branch..."
& "git" pull --ff-only origin $Branch 2>&1 | ForEach-Object { Write-Log $_ }
if ($LASTEXITCODE -ne 0) {
    Write-Log "ff-only failed, resetting hard..."
    & "git" reset --hard origin/$Branch 2>&1 | ForEach-Object { Write-Log $_ }
    if ($LASTEXITCODE -ne 0) {
        Write-Log "git reset --hard failed (exit $LASTEXITCODE)"
        exit 1
    }
}

# Step 3: Syntax guard
$enginePy = Join-Path $AgentRoot "apps\engine"
$failed = $false
Get-ChildItem -Path $enginePy -Filter "*.py" -Recurse | ForEach-Object {
    $escaped = $_.FullName -replace "'", "''"
    $result = & "python" "-c" "import ast, sys; ast.parse(open(sys.argv[1]).read())" $_.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "SYNTAX ERROR in $($_.Name): rolling back"
        $failed = $true
    }
}
if ($failed) {
    Write-Log "Rolling back to previous commit..."
    & "git" reset --hard $prevHead 2>&1 | ForEach-Object { Write-Log $_ }
    exit 1
}

# Step 4: Reinstall Python deps
Write-Log "Reinstalling Python deps..."
$venvPython = Join-Path $VenvRoot "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Log "Creating venv..."
    & "uv" venv $VenvRoot 2>&1 | ForEach-Object { Write-Log $_ }
}
$reqFile = Join-Path $AgentRoot "apps\engine\requirements.txt"
& "uv" "pip" "install" "--python" $venvPython "-r" $reqFile 2>&1 | ForEach-Object { Write-Log $_ }

# Step 5: Update content-hash stamp (desktop rebuild not applicable for cloned repo without node_modules)
# Desktop rebuild requires npm/npx which is only available in the developer's environment.
# When desktop source changes significantly, a new installer is distributed separately.
$desktopSrc = Join-Path $AgentRoot "apps\desktop"
$stampPath = if ($DesktopStampPath) { $DesktopStampPath } else { Join-Path $env:LOCALAPPDATA "novelforge\desktop-build-stamp.json" }
$hash = Compute-ContentHash $desktopSrc
if ($hash) {
    $newStamp = @{ contentHash = $hash; builtAt = (Get-Date -Format o) } | ConvertTo-Json
    $newStamp | Out-File -FilePath $stampPath -Encoding utf8
    Write-Log "Desktop content-hash stamp updated"
}

# Step 6: Launch (use original install path passed as -ExePath)
$launchExe = if ($ExePath) { $ExePath } else {
    # Fallback: try common locations
    $candidate = Join-Path (Split-Path $AgentRoot) "NovelForge.exe"
    if (-not (Test-Path $candidate)) { $candidate = Join-Path $desktopSrc "release\win-unpacked\NovelForge.exe" }
    $candidate
}
if (Test-Path $launchExe) {
    Write-Log "Launching $launchExe"
    Start-Process -FilePath $launchExe
} else {
    Write-Log "ERROR: NovelForge.exe not found — tried: $launchExe"
    exit 1
}

Write-Log "=== Update completed at $(Get-Date -Format o) ==="
