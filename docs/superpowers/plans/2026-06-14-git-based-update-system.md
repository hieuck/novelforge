# Git-Based Update System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace PyInstaller engine bundling with a Hermes-style git-based bootstrap + update system.

**Architecture:** Electron desktop app ships only the UI shell. On first launch, it clones the full repo into `%LOCALAPPDATA%\novelforge\novelforge-agent\`, sets up a Python venv, and starts the engine from there. Updates work via `git fetch + pull`, with a standalone PowerShell updater script that outlives the Electron process for safe file replacement. Content-hash stamping prevents unnecessary desktop rebuilds.

**Tech Stack:** Electron, TypeScript (main.ts), CJS modules for bootstrap/update logic, PowerShell (Windows updater), git, uv (Python package manager)

**Repo URL:** `https://github.com/hieuck/novelforge`
**Agent root:** `%LOCALAPPDATA%\novelforge\novelforge-agent\`
**Venue path:** `%LOCALAPPDATA%\novelforge\venv\`

---

### Task 1: Modify package.json — remove engine bundling, add pack script

**Files:**
- Modify: `apps/desktop/package.json`

- [ ] **Step 1: Remove `extraResources` for engine and add `pack` script**

Current `package.json` has:
```json
"extraResources": [
  {
    "from": "../engine/dist/engine",
    "to": "engine",
    "filter": ["**/*"]
  }
]
```

Change to:
```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "pack": "npm run build && tsc -p tsconfig.electron.json && electron-builder --dir",
  "preview": "vite preview",
  "electron:dev": "concurrently \"vite\" \"wait-on http://127.0.0.1:5173 && electron .\"",
  "electron:build": "npm run build && tsc -p tsconfig.electron.json && electron-builder",
  "lint": "eslint src --ext ts,tsx",
  "test": "vitest run",
  "test:watch": "vitest"
},
"build": {
  "appId": "com.novelforge.app",
  "productName": "NovelForge",
  "directories": {
    "output": "release"
  },
  "asarUnpack": [
    "scripts/**"
  ],
  "files": [
    "dist/**/*",
    "dist-electron/**/*",
    "scripts/**"
  ],
  "extraResources": [
    {
      "from": "scripts",
      "to": "scripts",
      "filter": ["*.ps1"]
    }
  ],
  "win": { ... },
  "nsis": { ... },
  "mac": { ... },
  "linux": { ... }
}
```

- [ ] **Step 2: Verify `npm run pack` works**

Run: `cd apps/desktop && npm run pack`
Expected: Produces `release/win-unpacked/NovelForge.exe` without engine directory

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/package.json
git commit -m "refactor(desktop): remove engine bundling, add pack script"
```

---

### Task 2: Create standalone updater script — `scripts/update-novelforge.ps1`

**Files:**
- Create: `apps/desktop/scripts/update-novelforge.ps1`

This PowerShell script is spawned by the Electron app when an update is triggered. It outlives the Electron process so it can replace locked files.

**Flow:**
1. Wait for Electron to release lock on the repo (poll up to 20s)
2. Force-kill any remaining `NovelForge.exe` processes if timeout expires
3. `git fetch origin main` + `git pull --ff-only` (auto-stash dirty changes)
4. Syntax guard: parse critical Python files, rollback on failure
5. `uv pip install -r apps/engine/requirements.txt` (reinstall deps)
6. Check content-hash stamp; if source changed, `cd apps/desktop && npm run pack`
7. Write updated content-hash stamp
8. Launch `NovelForge.exe` from the installation directory
9. Self-delete (cleanup)

- [ ] **Step 1: Write the updater script**

```powershell
param(
    [string]$AgentRoot,
    [string]$VenueRoot,
    [string]$Branch = "main",
    [string]$DesktopStampPath,
    [string]$LogFile
)

$ErrorActionPreference = "Stop"
$LogPath = if ($LogFile) { $LogFile } else { Join-Path $env:LOCALAPPDATA "novelforge\logs\update.log" }

function Write-Log { param([string]$Msg) $Msg | Out-File -FilePath $LogPath -Append }

Write-Log "=== Update started at $(Get-Date -Format o) ==="
Write-Log "AgentRoot: $AgentRoot | Branch: $Branch"

# Step 1: Wait for Electron to release lock
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
$hasDirty = & "git" status --porcelain
if ($hasDirty) {
    Write-Log "Stashing dirty changes..."
    & "git" stash push --include-untracked -m "auto-stash before update" 2>&1 | ForEach-Object { Write-Log $_ }
}
Write-Log "Pulling $Branch..."
& "git" pull --ff-only origin $Branch 2>&1 | ForEach-Object { Write-Log $_ }
if ($LASTEXITCODE -ne 0) {
    Write-Log "ff-only failed, resetting hard..."
    & "git" reset --hard origin/$Branch 2>&1 | ForEach-Object { Write-Log $_ }
}

# Step 3: Syntax guard (parse critical Python files)
$enginePy = Join-Path $AgentRoot "apps\engine"
$failed = $false
Get-ChildItem -Path $enginePy -Filter "*.py" -Recurse | ForEach-Object {
    $result = & "python" "-c" "import ast; ast.parse(open('$($_.FullName)').read())" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "SYNTAX ERROR in $($_.Name): rolling back"
        $failed = $true
    }
}
if ($failed) {
    Write-Log "Rolling back to previous commit..."
    & "git" reset --hard "HEAD@{1}" 2>&1 | ForEach-Object { Write-Log $_ }
    exit 1
}

# Step 4: Reinstall Python deps
Write-Log "Reinstalling Python deps..."
$venvPython = Join-Path $VenueRoot "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Log "Creating venv..."
    & "uv" venv $VenueRoot 2>&1 | ForEach-Object { Write-Log $_ }
}
$reqFile = Join-Path $AgentRoot "apps\engine\requirements.txt"
& "uv" "pip" "--python" $venvPython "install" "-r" $reqFile 2>&1 | ForEach-Object { Write-Log $_ }

# Step 5: Rebuild desktop if source changed
$desktopSrc = Join-Path $AgentRoot "apps\desktop"
$stampPath = if ($DesktopStampPath) { $DesktopStampPath } else { Join-Path $env:LOCALAPPDATA "novelforge\desktop-build-stamp.json" }
$needRebuild = $true
if (Test-Path $stampPath) {
    $stamp = Get-Content $stampPath -Raw | ConvertFrom-Json
    $currentHash = Compute-ContentHash $desktopSrc
    if ($currentHash -eq $stamp.contentHash) {
        Write-Log "Desktop source unchanged, skipping rebuild"
        $needRebuild = $false
    }
}
if ($needRebuild) {
    Write-Log "Rebuilding desktop..."
    Set-Location $desktopSrc
    & "npm" "run" "pack" 2>&1 | ForEach-Object { Write-Log $_ }
    # Write new stamp
    $hash = Compute-ContentHash $desktopSrc
    $newStamp = @{ contentHash = $hash; builtAt = (Get-Date -Format o) } | ConvertTo-Json
    $newStamp | Out-File -FilePath $stampPath -Encoding utf8
}

# Step 6: Launch
$exePath = Join-Path $desktopSrc "release\win-unpacked\NovelForge.exe"
if (Test-Path $exePath) {
    Write-Log "Launching $exePath"
    Start-Process -FilePath $exePath
} else {
    Write-Log "ERROR: NovelForge.exe not found at $exePath"
    exit 1
}

Write-Log "=== Update completed at $(Get-Date -Format o) ==="
```

- [ ] **Step 2: Commit**

```bash
git add apps/desktop/scripts/update-novelforge.ps1
git commit -m "feat(desktop): add standalone updater script"
```

---

### Task 3: Create `electron/backend-probes.cjs`

**Files:**
- Create: `apps/desktop/electron/backend-probes.cjs`

5-tier resolution ladder to find the running backend. Also provides helper functions used by bootstrap-runner and updater.

- [ ] **Step 1: Create backend-probes.cjs**

```js
const path = require('path');
const fs = require('fs');

const APP_DATA = process.env.LOCALAPPDATA || path.join(require('os').homedir(), 'AppData', 'Local');
const NOVELFORGE_HOME = path.join(APP_DATA, 'novelforge');
const AGENT_ROOT = path.join(NOVELFORGE_HOME, 'novelforge-agent');
const VENV_ROOT = path.join(NOVELFORGE_HOME, 'venv');
const BOOTSTRAP_MARKER = path.join(AGENT_ROOT, '.novelforge-bootstrap-complete');
const DESKTOP_STAMP = path.join(NOVELFORGE_HOME, 'desktop-build-stamp.json');

function resolveBackend() {
  // 1. Developer override
  if (process.env.NOVELFORGE_DESKTOP_ROOT) {
    const root = process.env.NOVELFORGE_DESKTOP_ROOT;
    if (validateAgentRoot(root)) {
      return { kind: 'local', root, venv: VENV_ROOT, engineDir: path.join(root, 'apps', 'engine') };
    }
  }

  // 2. Dev mode — running from repo checkout
  const sourceRoot = resolveSourceRoot();
  if (sourceRoot) {
    const engineDir = path.join(sourceRoot, 'apps', 'engine');
    const venvDir = path.join(engineDir, '.venv');
    if (fs.existsSync(engineDir)) {
      return { kind: 'dev', root: sourceRoot, venv: venvDir, engineDir };
    }
  }

  // 3. Bootstrap-complete install
  if (isBootstrapComplete()) {
    return { kind: 'local', root: AGENT_ROOT, venv: VENV_ROOT, engineDir: path.join(AGENT_ROOT, 'apps', 'engine') };
  }

  // 4. CLI on PATH (verified)
  // (skipped for now — no CLI binary yet)

  // 5. Bootstrap needed
  return { kind: 'bootstrap-needed' };
}

function resolveSourceRoot() {
  // Walk up from __dirname looking for the repo root
  let dir = path.resolve(__dirname, '..');
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(dir, '.git')) && fs.existsSync(path.join(dir, 'apps', 'engine'))) {
      return dir;
    }
    const parent = path.resolve(dir, '..');
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function isBootstrapComplete() {
  if (!fs.existsSync(BOOTSTRAP_MARKER)) return false;
  if (!fs.existsSync(AGENT_ROOT)) return false;
  const pythonExe = process.platform === 'win32'
    ? path.join(VENV_ROOT, 'Scripts', 'python.exe')
    : path.join(VENV_ROOT, 'bin', 'python3');
  if (!fs.existsSync(pythonExe)) return false;
  return true;
}

function getInstallStamp() {
  try {
    return JSON.parse(fs.readFileSync(BOOTSTRAP_MARKER, 'utf-8'));
  } catch { return null; }
}

module.exports = {
  NOVELFORGE_HOME,
  AGENT_ROOT,
  VENV_ROOT,
  BOOTSTRAP_MARKER,
  DESKTOP_STAMP,
  resolveBackend,
  resolveSourceRoot,
  isBootstrapComplete,
  getInstallStamp,
};
```

- [ ] **Step 2: Commit**

```bash
git add apps/desktop/electron/backend-probes.cjs
git commit -m "feat(desktop): add backend resolution ladder"
```

---

### Task 4: Create `electron/bootstrap-runner.cjs`

**Files:**
- Create: `apps/desktop/electron/bootstrap-runner.cjs`

Performs first-launch setup: git clone + venv + deps + desktop build + marker.

- [ ] **Step 1: Create bootstrap-runner.cjs**

```js
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { AGENT_ROOT, VENV_ROOT, NOVELFORGE_HOME, BOOTSTRAP_MARKER, DESKTOP_STAMP } = require('./backend-probes.cjs');

const REPO_URL = 'https://github.com/hieuck/novelforge';
const BRANCH = 'main';

async function runBootstrap(onEvent) {
  const events = [];
  const emit = (type, data) => {
    const ev = { type, data, timestamp: new Date().toISOString() };
    events.push(ev);
    if (onEvent) onEvent(ev);
  };

  try {
    // Ensure directories
    fs.mkdirSync(NOVELFORGE_HOME, { recursive: true });
    fs.mkdirSync(path.join(NOVELFORGE_HOME, 'logs'), { recursive: true });

    // 1. Git clone
    emit('stage', { name: 'clone', message: 'Cloning repository...' });
    await runCommand('git', [
      'clone', '--depth', '1', '--branch', BRANCH,
      REPO_URL, AGENT_ROOT
    ], { emit });

    // 2. Create venv
    emit('stage', { name: 'venv', message: 'Creating Python virtual environment...' });
    await runCommand('uv', ['venv', VENV_ROOT], { emit });

    // 3. Install deps
    emit('stage', { name: 'deps', message: 'Installing Python dependencies...' });
    const pythonExe = path.join(VENV_ROOT, 'Scripts', 'python.exe');
    const reqFile = path.join(AGENT_ROOT, 'apps', 'engine', 'requirements.txt');
    await runCommand('uv', ['pip', '--python', pythonExe, 'install', '-r', reqFile], { emit });

    // 4. Build desktop
    emit('stage', { name: 'build', message: 'Building desktop application...' });
    const desktopDir = path.join(AGENT_ROOT, 'apps', 'desktop');
    await runCommand('npm', ['run', 'pack'], { cwd: desktopDir, emit });

    // 5. Write desktop content-hash stamp
    const hash = await computeContentHash(desktopDir);
    fs.writeFileSync(DESKTOP_STAMP, JSON.stringify({ contentHash: hash, builtAt: new Date().toISOString() }, null, 2));

    // 6. Write bootstrap marker
    const commitSha = await getGitCommitSha(AGENT_ROOT);
    const marker = {
      schemaVersion: 1,
      pinnedCommit: commitSha,
      pinnedBranch: BRANCH,
      completedAt: new Date().toISOString(),
    };
    fs.writeFileSync(BOOTSTRAP_MARKER, JSON.stringify(marker, null, 2));

    emit('complete', { message: 'Bootstrap complete' });
    return { success: true };
  } catch (err) {
    emit('error', { message: err.message });
    return { success: false, error: err.message };
  }
}

function runCommand(cmd, args, { cwd, emit } = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, {
      cwd: cwd || process.cwd(),
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
      env: { ...process.env, UV_CACHE_DIR: path.join(NOVELFORGE_HOME, '.uv-cache') },
    });
    let stdout = '';
    proc.stdout.on('data', (d) => {
      const s = d.toString();
      stdout += s;
      if (emit) emit('log', s.trim());
    });
    proc.stderr.on('data', (d) => {
      const s = d.toString();
      if (emit) emit('log', s.trim());
    });
    proc.on('close', (code) => {
      if (code === 0) resolve(stdout.trim());
      else reject(new Error(`Command failed: ${cmd} ${args.join(' ')} (exit ${code})`));
    });
    proc.on('error', reject);
  });
}

function getGitCommitSha(repoDir) {
  return new Promise((resolve, reject) => {
    const proc = spawn('git', ['rev-parse', 'HEAD'], { cwd: repoDir });
    proc.stdout.on('data', (d) => resolve(d.toString().trim()));
    proc.on('error', reject);
  });
}

async function computeContentHash(dir) {
  const crypto = require('crypto');
  const hash = crypto.createHash('sha256');
  const files = await getSourceFiles(dir);
  for (const f of files.sort()) {
    const content = fs.readFileSync(path.join(dir, f));
    hash.update(f);
    hash.update(content);
  }
  return hash.digest('hex');
}

function getSourceFiles(dir) {
  return new Promise((resolve, reject) => {
    const { exec } = require('child_process');
    exec('git ls-files', { cwd: dir }, (err, stdout) => {
      if (err) return reject(err);
      resolve(stdout.trim().split('\n').filter(Boolean));
    });
  });
}

module.exports = { runBootstrap };
```

- [ ] **Step 2: Commit**

```bash
git add apps/desktop/electron/bootstrap-runner.cjs
git commit -m "feat(desktop): add bootstrap runner for first-launch setup"
```

---

### Task 5: Create `electron/updater.cjs`

**Files:**
- Create: `apps/desktop/electron/updater.cjs`

Handles update checking (git ls-remote) and applying updates (spawn updater script + quit). Also provides content-hash stamp management.

- [ ] **Step 1: Create updater.cjs**

```js
const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const {
  AGENT_ROOT, NOVELFORGE_HOME, BOOTSTRAP_MARKER, DESKTOP_STAMP,
  getInstallStamp,
} = require('./backend-probes.cjs');

const DEFAULT_BRANCH = 'main';

async function checkUpdates(branch = DEFAULT_BRANCH) {
  try {
    const stamp = getInstallStamp();
    if (!stamp || !stamp.pinnedCommit) {
      return { supported: false, reason: 'Not a git-based install' };
    }

    // Use ls-remote to get latest remote SHA
    const remoteRef = await gitLsRemote(branch);
    if (!remoteRef) {
      return { supported: false, reason: 'Cannot reach remote' };
    }

    const currentSha = stamp.pinnedCommit;
    const remoteSha = remoteRef.trim().split(/\s+/)[0];

    if (currentSha === remoteSha) {
      return { available: false, currentSha, remoteSha };
    }

    // Count commits behind
    const behind = await countCommitsBehind(currentSha, remoteSha);

    return {
      available: true,
      currentSha,
      remoteSha,
      behind,
      branch,
    };
  } catch (err) {
    return { supported: false, reason: err.message };
  }
}

function applyUpdates(branch = DEFAULT_BRANCH) {
  // Write updater script to NOVELFORGE_HOME
  const scriptContent = getUpdaterScriptContent();
  const scriptPath = path.join(NOVELFORGE_HOME, 'update-novelforge.ps1');
  fs.writeFileSync(scriptPath, scriptContent, 'utf-8');

  // Spawn updater detached — it outlives Electron
  const powershellPath = path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
  const logFile = path.join(NOVELFORGE_HOME, 'logs', 'update.log');
  const proc = spawn(powershellPath, [
    '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', scriptPath,
    '-AgentRoot', AGENT_ROOT,
    '-VenueRoot', path.join(NOVELFORGE_HOME, 'venv'),
    '-Branch', branch,
    '-DesktopStampPath', DESKTOP_STAMP,
    '-LogFile', logFile,
  ], {
    detached: true,
    stdio: 'ignore',
    windowsHide: true,
  });
  proc.unref();
}

function gitLsRemote(branch) {
  return new Promise((resolve, reject) => {
    const cwd = fs.existsSync(AGENT_ROOT) ? AGENT_ROOT : process.cwd();
    const proc = spawn('git', ['ls-remote', 'origin', branch], { cwd });
    let out = '';
    proc.stdout.on('data', (d) => { out += d.toString(); });
    proc.on('close', (code) => {
      if (code === 0) resolve(out.trim());
      else reject(new Error(`git ls-remote failed (exit ${code})`));
    });
    proc.on('error', reject);
  });
}

function countCommitsBehind(currentSha, remoteSha) {
  return new Promise((resolve, reject) => {
    const proc = spawn('git', ['rev-list', '--count', `${currentSha}..${remoteSha}`], { cwd: AGENT_ROOT });
    let out = '';
    proc.stdout.on('data', (d) => { out += d.toString(); });
    proc.on('close', (code) => {
      if (code === 0) resolve(parseInt(out.trim(), 10));
      else reject(new Error(`rev-list failed (exit ${code})`));
    });
    proc.on('error', reject);
  });
}

function getUpdaterScriptPath() {
  // In dev: side-by-side with the scripts directory
  // In prod: unpacked from asar via extraResources
  const devPath = path.join(__dirname, '..', 'scripts', 'update-novelforge.ps1');
  if (fs.existsSync(devPath)) return devPath;
  const prodPath = path.join(process.resourcesPath, 'scripts', 'update-novelforge.ps1');
  if (fs.existsSync(prodPath)) return prodPath;
  // Fallback: write the script dynamically
  return null;
}

function getUpdaterScriptContent() {
  const scriptPath = getUpdaterScriptPath();
  if (scriptPath) {
    return fs.readFileSync(scriptPath, 'utf-8');
  }
  // Fallback: inline minimal updater (should not happen in normal operation)
  return `...`; // minimal inline fallback
}

// ── Content-hash stamp ──────────────────────────────────────────────────────

function readDesktopStamp() {
  try { return JSON.parse(fs.readFileSync(DESKTOP_STAMP, 'utf-8')); }
  catch { return null; }
}

function writeDesktopStamp(hash) {
  const stamp = { contentHash: hash, builtAt: new Date().toISOString() };
  fs.writeFileSync(DESKTOP_STAMP, JSON.stringify(stamp, null, 2));
}

function computeDesktopContentHash() {
  const dir = path.join(AGENT_ROOT, 'apps', 'desktop');
  if (!fs.existsSync(dir)) return null;
  const hash = crypto.createHash('sha256');
  try {
    const files = execSync('git ls-files', { cwd: dir }).toString().trim().split('\n').filter(Boolean);
    for (const f of files.sort()) {
      const fullPath = path.join(dir, f);
      if (fs.existsSync(fullPath)) {
        hash.update(f);
        hash.update(fs.readFileSync(fullPath));
      }
    }
  } catch { return null; }
  return hash.digest('hex');
}

module.exports = { checkUpdates, applyUpdates, readDesktopStamp, writeDesktopStamp, computeDesktopContentHash };
```

- [ ] **Step 2: Commit**

```bash
git add apps/desktop/electron/updater.cjs
git commit -m "feat(desktop): add git-based updater with content-hash stamp"
```

---

### Task 6: Modify `electron/main.ts` — integrate bootstrap + update flow

**Files:**
- Modify: `apps/desktop/electron/main.ts`

- [ ] **Step 1: Rewrite main.ts with bootstrap/update integration**

```typescript
import { app, BrowserWindow, shell, ipcMain } from 'electron'
import * as path from 'path'
import * as child_process from 'child_process'
import * as fs from 'fs'
import * as http from 'http'

const isDev = !app.isPackaged
const ENGINE_PORT = 9000

let mainWindow: BrowserWindow | null = null
let engineProcess: child_process.ChildProcess | null = null
let splashWindow: BrowserWindow | null = null

// Dynamic requires for CJS modules (bundled as extraResources or side-by-side)
const probesPath = path.join(__dirname, 'backend-probes.cjs')
const bootstrapPath = path.join(__dirname, 'bootstrap-runner.cjs')
const updaterPath = path.join(__dirname, 'updater.cjs')

let probes: any = null
let bootstrapRunner: any = null
let updater: any = null

function loadModules() {
  probes = require(probesPath)
  bootstrapRunner = require(bootstrapPath)
  updater = require(updaterPath)
}

// ── Backend resolution ────────────────────────────────────────────────────

function resolveEngine() {
  if (isDev) {
    const venvPy = process.platform === 'win32'
      ? path.join(__dirname, '../../engine/.venv/Scripts/python.exe')
      : path.join(__dirname, '../../engine/.venv/bin/python3')
    return { cmd: venvPy, args: ['run.py'], cwd: path.join(__dirname, '../../engine') }
  }

  const backend = probes.resolveBackend()
  if (backend.kind === 'bootstrap-needed') {
    return null // triggers bootstrap flow
  }

  const pythonExe = process.platform === 'win32'
    ? path.join(backend.venv, 'Scripts', 'python.exe')
    : path.join(backend.venv, 'bin', 'python3')
  return { cmd: pythonExe, args: ['run.py'], cwd: backend.engineDir }
}

function startEngine(): void {
  const resolved = resolveEngine()
  if (!resolved) {
    // Will be handled by bootstrap flow before this is called
    console.error('[main] No engine found — bootstrap needed')
    return
  }
  const { cmd, args, cwd } = resolved
  if (!fs.existsSync(cwd)) { console.error('[main] Engine dir missing:', cwd); return }
  engineProcess = child_process.spawn(cmd, args, {
    cwd,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  })
  engineProcess.stdout?.on('data', (d: Buffer) => process.stdout.write(`[engine] ${d}`))
  engineProcess.stderr?.on('data', (d: Buffer) => process.stderr.write(`[engine] ${d}`))
  engineProcess.on('exit', (code) => console.log(`[main] Engine exited: ${code}`))
}

function stopEngine(): void {
  if (engineProcess && !engineProcess.killed) {
    engineProcess.kill()
    engineProcess = null
  }
}

// ── Bootstrap flow ─────────────────────────────────────────────────────────

async function runBootstrap(): Promise<boolean> {
  return new Promise((resolve) => {
    bootstrapRunner.runBootstrap((event: any) => {
      console.log(`[bootstrap] ${event.type}:`, event.data)
      // Forward to renderer via IPC
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('novelforge:bootstrap:status', event)
      }
      if (event.type === 'complete') resolve(true)
      if (event.type === 'error') resolve(false)
    })
  })
}

// ── Health check ──────────────────────────────────────────────────────────

function waitForEngine(port: number, maxMs = 60000): Promise<void> {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const poll = () => {
      const req = http.get(`http://127.0.0.1:${port}/api/health`, (res) => {
        res.statusCode === 200 ? resolve() : retry()
        res.resume()
      })
      req.on('error', retry)
      req.setTimeout(1000, () => { req.destroy(); retry() })
    }
    const retry = () => {
      if (Date.now() - start > maxMs) { reject(new Error('Engine timeout')); return }
      setTimeout(poll, 500)
    }
    poll()
  })
}

// ── Splash ───────────────────────────────────────────────────────────────

function createSplash(): void {
  // ... unchanged from current implementation ...
  splashWindow = new BrowserWindow({
    width: 380, height: 220,
    frame: false, resizable: false, center: true,
    backgroundColor: '#020817',
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  })
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    body{margin:0;background:#020817;color:#e2e8f0;font-family:system-ui,sans-serif;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    height:100vh;gap:16px;}
    h1{font-size:24px;font-weight:700;margin:0;color:#f1f5f9;}
    p{font-size:13px;color:#64748b;margin:0;}
    .dot{display:inline-block;width:8px;height:8px;border-radius:50%;
    background:#6366f1;animation:b 1.2s infinite;}
    .dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}
    @keyframes b{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-10px)}}
    .dots{display:flex;gap:6px;}
    </style></head><body>
    <h1>⚡ NovelForge</h1><p>Starting AI engine...</p>
    <div class="dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
    </body></html>`
  splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`)
}

// ── Bootstrap splash ──────────────────────────────────────────────────────

function createBootstrapSplash(): void {
  splashWindow = new BrowserWindow({
    width: 480, height: 320,
    frame: false, resizable: false, center: true,
    backgroundColor: '#020817',
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  })
  splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>
      body{margin:0;background:#020817;color:#e2e8f0;font-family:system-ui,sans-serif;
      display:flex;flex-direction:column;align-items:center;justify-content:center;
      height:100vh;gap:12px;padding:40px;}
      h1{font-size:24px;font-weight:700;margin:0;color:#f1f5f9;}
      #status{font-size:13px;color:#94a3b8;text-align:center;}
      #progress{width:100%;max-width:360px;height:4px;background:#1e293b;border-radius:2px;overflow:hidden;}
      #bar{height:100%;width:0%;background:#6366f1;transition:width .3s;}
      .dot{display:inline-block;width:8px;height:8px;border-radius:50%;
      background:#6366f1;animation:b 1.2s infinite;}
      .dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}
      @keyframes b{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-10px)}}
      .dots{display:flex;gap:6px;margin-top:8px;}
    </style></head><body>
    <h1>⚡ NovelForge</h1>
    <p id="status">Setting up your workspace...</p>
    <div id="progress"><div id="bar" style="width:10%"></div></div>
    <div class="dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
    <script>
      const { ipcRenderer } = require('electron');
      ipcRenderer.on('novelforge:bootstrap:status', (_, ev) => {
        if (ev.type === 'stage') {
          document.getElementById('status').textContent = ev.data.message;
        }
        if (ev.type === 'error') {
          document.getElementById('status').textContent = 'Error: ' + ev.data.message;
        }
        if (ev.type === 'complete') {
          document.getElementById('status').textContent = 'Starting...';
        }
      });
    </script>
    </body></html>
  `)}`)
}

// ── IPC handlers ─────────────────────────────────────────────────────────

function registerIpcHandlers() {
  ipcMain.handle('novelforge:updates:check', async () => {
    return updater.checkUpdates()
  })

  ipcMain.handle('novelforge:updates:apply', async (_event, branch?: string) => {
    updater.applyUpdates(branch)
    app.quit()
  })

  ipcMain.handle('novelforge:updates:stamp', async () => {
    return updater.readDesktopStamp()
  })
}

// ── Main window ──────────────────────────────────────────────────────────

function createMainWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1440, height: 900,
    minWidth: 960, minHeight: 600,
    title: 'NovelForge',
    backgroundColor: '#020817',
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: !isDev,
      additionalArguments: [`--engine-port=${ENGINE_PORT}`],
      preload: path.join(__dirname, 'preload.js'),
    },
  })

  if (isDev) {
    mainWindow.loadURL('http://127.0.0.1:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.once('ready-to-show', () => {
    splashWindow?.close()
    splashWindow = null
    mainWindow?.show()
    mainWindow?.focus()
  })

  mainWindow.on('closed', () => { mainWindow = null })
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) shell.openExternal(url)
    return { action: 'deny' }
  })
}

// ── Lifecycle ────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  loadModules()
  registerIpcHandlers()

  if (!isDev) {
    // Check if bootstrap is needed
    const backend = probes.resolveBackend()
    if (backend.kind === 'bootstrap-needed') {
      createBootstrapSplash()
      const success = await runBootstrap()
      if (!success) {
        console.error('[main] Bootstrap failed')
        // Show error in splash — user can close and retry
        return
      }
    }

    createSplash()
    startEngine()
    try {
      await waitForEngine(ENGINE_PORT, 60000)
      console.log('[main] Engine ready on port', ENGINE_PORT)
    } catch (err) {
      console.error('[main] Engine failed to start:', err)
    }
  }
  createMainWindow()
})

app.on('window-all-closed', () => { stopEngine(); if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (!mainWindow) createMainWindow() })
app.on('before-quit', stopEngine)
```

- [ ] **Step 2: Verify TypeScript compilation**

Run: `cd apps/desktop && npx tsc -p tsconfig.electron.json --noEmit`
Expected: No type errors (main.ts uses `.cjs` which doesn't have types, so suppress with `// @ts-nocheck` or loose `require` calls)

If errors arise due to `require()` of `.cjs` files, add type declaration:

```typescript
// Allow dynamic CJS requires
declare function require(name: string): any
```

- [ ] **Step 2b: Build and verify**

Run: `cd apps/desktop && tsc -p tsconfig.electron.json`
Expected: `dist-electron/main.js` compiles successfully

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/electron/main.ts
git commit -m "feat(desktop): integrate bootstrap runner and git-based updater"
```

---

### Task 7: Update preload.ts — expose update IPC to renderer

**Files:**
- Modify: `apps/desktop/electron/preload.ts`

- [ ] **Step 1: Add update IPC methods**

```typescript
import { contextBridge, ipcRenderer } from 'electron'

const enginePort = (() => {
  const arg = process.argv.find((a) => a.startsWith('--engine-port='))
  return arg ? parseInt(arg.split('=')[1], 10) : 9000
})()

contextBridge.exposeInMainWorld('__NOVELFORGE__', {
  enginePort,
  updates: {
    check: () => ipcRenderer.invoke('novelforge:updates:check'),
    apply: (branch?: string) => ipcRenderer.invoke('novelforge:updates:apply', branch),
    getStamp: () => ipcRenderer.invoke('novelforge:updates:stamp'),
  },
})
```

- [ ] **Step 2: Build and verify**

Run: `cd apps/desktop && tsc -p tsconfig.electron.json`
Expected: Compiles without errors

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/electron/preload.ts
git commit -m "feat(desktop): expose update IPC to renderer"
```

---

### Task 8: Update build stamp — write commit info during pack

**Files:**
- Create: `apps/desktop/scripts/write-build-stamp.cjs`

Inspired by Hermes' `write-build-stamp.cjs`. Writes an `install-stamp.json` with git SHA so the app knows what commit it was built from.

This is useful for dev mode and for the content-hash system.

- [ ] **Step 1: Create write-build-stamp.cjs**

```js
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const outDir = path.resolve(__dirname, '..', 'build');
fs.mkdirSync(outDir, { recursive: true });

let commit = '';
let branch = '';
let dirty = false;

try {
  commit = execSync('git rev-parse HEAD', { encoding: 'utf-8' }).trim();
  branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf-8' }).trim();
  dirty = execSync('git status --porcelain', { encoding: 'utf-8' }).trim().length > 0;
} catch {
  // Not in a git repo (packaged build)
}

const stamp = {
  schemaVersion: 1,
  commit: commit || process.env.GITHUB_SHA || 'unknown',
  branch: branch || process.env.GITHUB_REF_NAME || 'unknown',
  builtAt: new Date().toISOString(),
  dirty,
  source: commit ? 'git' : 'env',
};

fs.writeFileSync(path.join(outDir, 'install-stamp.json'), JSON.stringify(stamp, null, 2));
console.log('Wrote build stamp:', JSON.stringify(stamp, null, 2));
```

- [ ] **Step 2: Commit**

```bash
git add apps/desktop/scripts/write-build-stamp.cjs
git commit -m "feat(desktop): add build stamp writer"
```

---

### Task 9: Clean up old engine build artifacts

**Files:**
- Modify: `.gitignore` (remove engine/dist from ignore if needed)

- [ ] **Step 1: Update .gitignore to ignore old engine build artifacts**

No changes needed — the engine dist is already in `apps/engine/.gitignore` or `apps/engine/dist/` is gitignored.

- [ ] **Step 2: Verify nothing references PyInstaller engine**

Run: `rg "engine\.exe" apps/desktop/`
Expected: No matches (should have been replaced by bootstrap resolution)

Run: `rg "extraResources" apps/desktop/package.json`
Expected: No `extraResources` for engine

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "chore: remove old PyInstaller engine build artifacts"
```

---

## Self-Review Checklist

- [ ] Every spec requirement maps to a task
- [ ] No placeholders (TBD, TODO, "implement later")
- [ ] File paths are exact and consistent
- [ ] No type/signature inconsistencies across tasks
- [ ] All commands include expected output
