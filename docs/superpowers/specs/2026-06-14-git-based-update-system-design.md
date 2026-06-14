# Git-Based Update System for NovelForge Desktop

**Date:** 2026-06-14
**Status:** Draft
**Inspired by:** Hermes Agent (NousResearch) — git-based bootstrap + update pattern

## Problem

Current NovelForge Desktop bundles the Python engine via PyInstaller (`engine.exe`) inside the Electron installer. This means:
- Every update requires downloading a new full installer (~100+ MB)
- The engine cannot be updated independently from the desktop shell
- No automatic update path — user must manually download and reinstall
- PyInstaller adds build complexity and ~15MB to each release

## Solution

Adopt the Hermes Agent pattern:
- **Ship only the Electron shell** in the installer (thin client)
- **Full git clone** at first launch into `%LOCALAPPDATA%\novelforge\novelforge-agent\`
- **Git-based updates**: `git fetch + pull` instead of downloading new installers
- **Content-hash stamp** to skip unnecessary desktop rebuilds
- **Standalone updater script** (PowerShell) that outlives the Electron process for safe file replacement

## Architecture

### Directory Layout

```
%LOCALAPPDATA%\novelforge\
├── novelforge-agent\                   ← Full git clone of hieuck/novelforge
│   ├── apps\engine\                    ← Python backend (FastAPI + uvicorn)
│   ├── apps\desktop\                   ← Electron source (for rebuild)
│   ├── docs\
│   ├── scripts\
│   ├── .git\
│   ├── pyproject.toml
│   └── .novelforge-bootstrap-complete  ← JSON marker { pinnedCommit, pinnedBranch, ... }
├── venv\                               ← Python virtual environment
├── logs\
│   ├── desktop.log
│   └── engine.log
├── config.yaml                         ← User configuration
├── desktop-build-stamp.json            ← Content-hash for rebuild skipping
└── update-novelforge.ps1              ← Standalone updater (written when needed)
```

### Component Tree (apps/desktop/)

```
electron/
├── main.cjs                  ← Modified: add bootstrap + update flow
├── bootstrap-runner.cjs      ← NEW: first-launch git clone + setup
├── updater.cjs               ← NEW: checkUpdates + applyUpdates
└── backend-probes.cjs        ← NEW: resolve backend from multiple sources

scripts/
└── update-novelforge.ps1     ← NEW: standalone updater script
```

## Detailed Design

### 1. Backend Resolution (`electron/backend-probes.cjs`)

5-tier fallthrough ladder to locate the running backend:

1. **`NOVELFORGE_DESKTOP_ROOT` env var** — developer override, skip bootstrap entirely
2. **`SOURCE_REPO_ROOT`** — running `npm run dev` from a checkout; detect by checking for `.git` in parent dirs
3. **`%LOCALAPPDATA%/novelforge/novelforge-agent/` with valid bootstrap marker** — normal installed path
4. **`novelforge` on PATH** — only if a CLI binary exists AND passes smoke test (`novelforge --version`)
5. **`{ kind: 'bootstrap-needed' }`** — sentinel that triggers first-launch installer

**Marker schema** (`.novelforge-bootstrap-complete`):
```json
{
  "schemaVersion": 1,
  "pinnedCommit": "abc123def...",
  "pinnedBranch": "main",
  "completedAt": "2026-06-14T12:00:00Z"
}
```

### 2. Bootstrap Runner (`electron/bootstrap-runner.cjs`)

Triggered when backend resolution returns `bootstrap-needed`.

**Flow:**
1. Create target dir `%LOCALAPPDATA%\novelforge\novelforge-agent\`
2. **Shallow clone**: `git clone --depth 1 --branch main https://github.com/hieuck/novelforge.git <target>`
3. **Setup venv**: `uv venv` + `uv pip install -e apps/engine`
4. **Build desktop**: `cd apps/desktop && npm run pack` (produces `release/win-unpacked/NovelForge.exe`)
5. **Write bootstrap marker** with current commit SHA
6. **Stream progress** to renderer via IPC events: stage name, log lines, completion/error

**Error handling:**
- If clone fails: retry once after 5s; if still fails, show error with "Retry" button
- If npm run pack fails: purge cached Electron zip, retry once
- All stages emit IPC events for real-time UI (progress bar + status text)

### 3. Updater (`electron/updater.cjs`)

#### Check for Updates

```js
async function checkUpdates(branch = 'main') {
  // Run git ls-remote to get latest remote SHA
  const remoteSha = await git(['ls-remote', 'origin', branch]);
  // Compare with pinnedCommit from bootstrap marker
  if (remoteSha !== pinnedCommit) {
    return { available: true, currentSha, remoteSha, behind: commitCount };
  }
  return { available: false };
}
```

- Only checks `origin/main` by default
- Returns commit log between current HEAD and remote for changelog display
- No GitHub REST API calls — pure git protocol

#### Apply Updates

```js
async function applyUpdates() {
  // 1. Write update-novelforge.ps1 to %LOCALAPPDATA%\novelforge\
  // 2. Spawn update-novelforge.ps1 DETACHED (can outlive Electron)
  // 3. app.quit()
}
```

The Electron app does NOT mutate itself. It hands off to the standalone script.

#### Content-Hash Stamp

File: `%LOCALAPPDATA%\novelforge\desktop-build-stamp.json`
```json
{
  "contentHash": "<sha256 of all desktop source files>",
  "builtAt": "2026-06-14T12:00:00Z"
}
```

- Computed by hashing all files in `apps/desktop/` (respecting `.gitignore`)
- Checked before rebuild — if hash matches, skip `npm run pack`
- Written after successful build

### 4. Standalone Updater Script (`scripts/update-novelforge.ps1`)

This script is embedded in the Electron app as a resource. When an update is triggered:

1. **Wait for lock release**: Poll `%LOCALAPPDATA%\novelforge\novelforge-agent\` for up to 20s until no process holds it open
2. **Force-kill stragglers**: If timeout expires, `taskkill /f /im NovelForge.exe`
3. **Git pull**: `cd novelforge-agent && git fetch origin main && git pull --ff-only`
   - Auto-stash local changes if dirty
   - If `--ff-only` fails (diverged history), fall back to `git reset --hard origin/main`
4. **Syntax guard**: Parse critical Python files with `python -c "import ast; ast.parse(...)"` — if bad commit pulled, auto-rollback to pre-pull SHA
5. **Reinstall Python deps**: `uv pip install -e apps/engine`
6. **Rebuild desktop**: Check content-hash stamp; if source changed, `cd apps/desktop && npm run pack`
7. **Launch**: `start <path-to-novelforge-exe>`
8. **Self-delete**: Remove `update-novelforge.ps1`

### 5. IPC Handlers (main.cjs)

| Channel | Direction | Purpose |
|---|---|---|
| `novelforge:updates:check` | Renderer → Main | Trigger update check |
| `novelforge:updates:apply` | Renderer → Main | Trigger update application |
| `novelforge:updates:status` | Main → Renderer | Stream check/apply progress |
| `novelforge:bootstrap:status` | Main → Renderer | Stream bootstrap progress |
| `novelforge:backend:status` | Main → Renderer | Backend readiness (port, PID) |

## Changes to Existing Files

### `apps/desktop/package.json`

- Remove `extraResources` entry for `engine/`
- Keep electron-builder targets: NSIS (Windows)
- Add `build.extraResources` empty (no bundled engine)

### `apps/desktop/electron/main.cjs`

- Import `bootstrap-runner.cjs`, `updater.cjs`, `backend-probes.cjs`
- Replace static backend path resolution with the 5-tier ladder
- Call `ensureRuntime()` on bootstrap-needed
- Register IPC handlers for update + bootstrap events
- Add `startHermesBackend()` that spawns from cloned repo path

## What Gets Removed

- `scripts/build_engine.py` — no longer needed (PyInstaller deprecated)
- `apps/engine/dist/` — build output; remove from VCS ignore
- `extraResources` engine path in electron-builder config
- Any references to `engine.exe` in `main.cjs`

## Non-Goals

- Cross-platform updater for macOS/Linux (future)
- Tauri-based updater binary (future; PowerShell is initial approach)
- Delta updates / binary diff (git handles this naturally)
- Auto-update in background (user-initiated via UI button)
- Mobile app updates

## Open Questions

- [ ] Should the update-novelforge.ps1 be embedded as a binary resource or written dynamically?
- [ ] What timeout for forced kill during update? (Initial: 20s poll + 10s grace)

## Edge Cases

- **Offline**: Check for updates silently fails; UI shows "No internet"
- **Dirty checkout**: Auto-stash before pull; notify user of stashed changes
- **Bad commit pulled**: Syntax guard catches parse errors; auto-rollback
- **First launch with no internet**: Bootstrap fails; UI shows error + "Retry" button
- **Update while engine is running**: Engine PID tracked; killed before venv update
- **Corrupt npm install**: Cache purge + retry once
