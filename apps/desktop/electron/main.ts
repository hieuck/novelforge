import { app, BrowserWindow, shell } from 'electron'
import * as path from 'path'
import * as child_process from 'child_process'
import * as fs from 'fs'
import * as http from 'http'

const isDev = !app.isPackaged
const ENGINE_PORT = 9000

let mainWindow: BrowserWindow | null = null
let engineProcess: child_process.ChildProcess | null = null
let splashWindow: BrowserWindow | null = null

// ── Engine spawn ──────────────────────────────────────────────────────────────

function findEngine(): { cmd: string; args: string[]; cwd: string } {
  if (isDev) {
    const venvPy = process.platform === 'win32'
      ? path.join(__dirname, '../../engine/.venv/Scripts/python.exe')
      : path.join(__dirname, '../../engine/.venv/bin/python3')
    return { cmd: venvPy, args: ['run.py'], cwd: path.join(__dirname, '../../engine') }
  }
  // Production: PyInstaller-built exe in extraResources
  const exeName = process.platform === 'win32' ? 'engine.exe' : 'engine'
  const engineExe = path.join(process.resourcesPath, 'engine', exeName)
  if (fs.existsSync(engineExe)) {
    return { cmd: engineExe, args: [], cwd: path.join(process.resourcesPath, 'engine') }
  }
  // Fallback: system Python
  return {
    cmd: process.platform === 'win32' ? 'python' : 'python3',
    args: ['run.py'],
    cwd: path.join(process.resourcesPath, 'engine'),
  }
}

function startEngine(): void {
  const { cmd, args, cwd } = findEngine()
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

// ── Health check ──────────────────────────────────────────────────────────────

function waitForEngine(port: number, maxMs = 30000): Promise<void> {
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

// ── Splash ────────────────────────────────────────────────────────────────────

function createSplash(): void {
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

// ── Main window ───────────────────────────────────────────────────────────────

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

// ── Lifecycle ─────────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  if (!isDev) {
    createSplash()
    startEngine()
    try {
      await waitForEngine(ENGINE_PORT, 30000)
      console.log('[main] Engine ready on port', ENGINE_PORT)
    } catch (err) {
      console.error('[main] Engine failed to start:', err)
      // Proceed anyway — renderer will show API errors
    }
  }
  createMainWindow()
})

app.on('window-all-closed', () => { stopEngine(); if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (!mainWindow) createMainWindow() })
app.on('before-quit', stopEngine)
