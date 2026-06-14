"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const path = __importStar(require("path"));
const child_process = __importStar(require("child_process"));
const fs = __importStar(require("fs"));
const http = __importStar(require("http"));
const isDev = !electron_1.app.isPackaged;
const ENGINE_PORT = 9000;
let mainWindow = null;
let engineProcess = null;
let splashWindow = null;
// ── Engine spawn ──────────────────────────────────────────────────────────────
function findEngine() {
    if (isDev) {
        const venvPy = process.platform === 'win32'
            ? path.join(__dirname, '../../engine/.venv/Scripts/python.exe')
            : path.join(__dirname, '../../engine/.venv/bin/python3');
        return { cmd: venvPy, args: ['run.py'], cwd: path.join(__dirname, '../../engine') };
    }
    // Production: PyInstaller-built exe in extraResources
    const exeName = process.platform === 'win32' ? 'engine.exe' : 'engine';
    const engineExe = path.join(process.resourcesPath, 'engine', exeName);
    if (fs.existsSync(engineExe)) {
        return { cmd: engineExe, args: [], cwd: path.join(process.resourcesPath, 'engine') };
    }
    // Fallback: system Python
    return {
        cmd: process.platform === 'win32' ? 'python' : 'python3',
        args: ['run.py'],
        cwd: path.join(process.resourcesPath, 'engine'),
    };
}
function startEngine() {
    const { cmd, args, cwd } = findEngine();
    if (!fs.existsSync(cwd)) {
        console.error('[main] Engine dir missing:', cwd);
        return;
    }
    engineProcess = child_process.spawn(cmd, args, {
        cwd,
        stdio: ['ignore', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
    });
    engineProcess.stdout?.on('data', (d) => process.stdout.write(`[engine] ${d}`));
    engineProcess.stderr?.on('data', (d) => process.stderr.write(`[engine] ${d}`));
    engineProcess.on('exit', (code) => console.log(`[main] Engine exited: ${code}`));
}
function stopEngine() {
    if (engineProcess && !engineProcess.killed) {
        engineProcess.kill();
        engineProcess = null;
    }
}
// ── Health check ──────────────────────────────────────────────────────────────
function waitForEngine(port, maxMs = 30000) {
    return new Promise((resolve, reject) => {
        const start = Date.now();
        const poll = () => {
            const req = http.get(`http://127.0.0.1:${port}/api/health`, (res) => {
                res.statusCode === 200 ? resolve() : retry();
                res.resume();
            });
            req.on('error', retry);
            req.setTimeout(1000, () => { req.destroy(); retry(); });
        };
        const retry = () => {
            if (Date.now() - start > maxMs) {
                reject(new Error('Engine timeout'));
                return;
            }
            setTimeout(poll, 500);
        };
        poll();
    });
}
// ── Splash ────────────────────────────────────────────────────────────────────
function createSplash() {
    splashWindow = new electron_1.BrowserWindow({
        width: 380, height: 220,
        frame: false, resizable: false, center: true,
        backgroundColor: '#020817',
        webPreferences: { nodeIntegration: false, contextIsolation: true },
    });
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
    </body></html>`;
    splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
}
// ── Main window ───────────────────────────────────────────────────────────────
function createMainWindow() {
    mainWindow = new electron_1.BrowserWindow({
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
    });
    if (isDev) {
        mainWindow.loadURL('http://127.0.0.1:5173');
    }
    else {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }
    mainWindow.once('ready-to-show', () => {
        splashWindow?.close();
        splashWindow = null;
        mainWindow?.show();
        mainWindow?.focus();
    });
    mainWindow.on('closed', () => { mainWindow = null; });
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith('http'))
            electron_1.shell.openExternal(url);
        return { action: 'deny' };
    });
}
// ── Lifecycle ─────────────────────────────────────────────────────────────────
electron_1.app.whenReady().then(async () => {
    if (!isDev) {
        createSplash();
        startEngine();
        try {
            await waitForEngine(ENGINE_PORT, 30000);
            console.log('[main] Engine ready on port', ENGINE_PORT);
        }
        catch (err) {
            console.error('[main] Engine failed to start:', err);
            // Proceed anyway — renderer will show API errors
        }
    }
    createMainWindow();
});
electron_1.app.on('window-all-closed', () => { stopEngine(); if (process.platform !== 'darwin')
    electron_1.app.quit(); });
electron_1.app.on('activate', () => { if (!mainWindow)
    createMainWindow(); });
electron_1.app.on('before-quit', stopEngine);
