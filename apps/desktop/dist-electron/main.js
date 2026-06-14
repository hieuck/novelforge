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
function loadCJS(name) {
    return require(path.join(__dirname, '../electron', `${name}.cjs`));
}
function resolveEngine() {
    if (isDev) {
        const venvPy = process.platform === 'win32'
            ? path.join(__dirname, '../../engine/.venv/Scripts/python.exe')
            : path.join(__dirname, '../../engine/.venv/bin/python3');
        return { cmd: venvPy, args: ['run.py'], cwd: path.join(__dirname, '../../engine') };
    }
    const probes = loadCJS('backend-probes');
    const backend = probes.resolveBackend();
    if (backend.kind === 'bootstrap-needed') {
        return null;
    }
    const pythonExe = process.platform === 'win32'
        ? path.join(backend.venv, 'Scripts', 'python.exe')
        : path.join(backend.venv, 'bin', 'python3');
    return { cmd: pythonExe, args: ['run.py'], cwd: backend.engineDir };
}
function startEngine() {
    const resolved = resolveEngine();
    if (!resolved) {
        console.error('[main] No engine found — bootstrap needed');
        return;
    }
    const { cmd, args, cwd } = resolved;
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
async function runBootstrap() {
    const bootstrap = loadCJS('bootstrap-runner');
    return new Promise((resolve) => {
        bootstrap.runBootstrap((event) => {
            console.log(`[bootstrap] ${event.type}:`, event.data);
            if (splashWindow && !splashWindow.isDestroyed()) {
                splashWindow.webContents.send('novelforge:bootstrap:status', event);
            }
            if (event.type === 'complete')
                resolve({ success: true });
            if (event.type === 'error')
                resolve({ success: false, error: event.data.message });
        });
    });
}
function createBootstrapSplash() {
    splashWindow = new electron_1.BrowserWindow({
        width: 480, height: 320,
        frame: false, resizable: false, center: true,
        backgroundColor: '#020817',
        webPreferences: { nodeIntegration: true, contextIsolation: false },
    });
    splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>
      body{margin:0;background:#020817;color:#e2e8f0;font-family:system-ui,sans-serif;
      display:flex;flex-direction:column;align-items:center;justify-content:center;
      height:100vh;gap:12px;padding:40px;}
      h1{font-size:24px;font-weight:700;margin:0;color:#f1f5f9;}
      #status{font-size:13px;color:#94a3b8;text-align:center;}
      #progress{width:100%;max-width:360px;height:4px;background:#1e293b;border-radius:2px;overflow:hidden;}
      #bar{height:100%;width:10%;background:#6366f1;transition:width .3s;}
    </style></head><body>
    <h1>⚡ NovelForge</h1>
    <p id="status">Setting up your workspace...</p>
    <div id="progress"><div id="bar"></div></div>
    <script>
      const { ipcRenderer } = require('electron');
      ipcRenderer.on('novelforge:bootstrap:status', (_, ev) => {
        if (ev.type === 'stage') document.getElementById('status').textContent = ev.data.message;
        if (ev.type === 'error') document.getElementById('status').textContent = 'Error: ' + ev.data.message;
        if (ev.type === 'complete') document.getElementById('status').textContent = 'Starting...';
      });
    </script>
    </body></html>
  `)}`);
}
function waitForEngine(port, maxMs = 60000) {
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
function registerIpcHandlers() {
    electron_1.ipcMain.handle('novelforge:updates:check', async () => {
        const updater = loadCJS('updater');
        return updater.checkUpdates();
    });
    electron_1.ipcMain.handle('novelforge:updates:apply', async (_event, branch) => {
        const updater = loadCJS('updater');
        updater.applyUpdates(branch);
        electron_1.app.quit();
    });
    electron_1.ipcMain.handle('novelforge:updates:stamp', async () => {
        const updater = loadCJS('updater');
        return updater.readDesktopStamp();
    });
}
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
function showErrorDialog(title, message) {
    splashWindow?.close();
    splashWindow = null;
    const { dialog } = require('electron');
    dialog.showErrorBox(title, message);
    electron_1.app.quit();
}
electron_1.app.whenReady().then(async () => {
    registerIpcHandlers();
    if (!isDev) {
        const probes = loadCJS('backend-probes');
        const backend = probes.resolveBackend();
        if (backend.kind === 'bootstrap-needed') {
            createBootstrapSplash();
            const result = await runBootstrap();
            if (!result.success) {
                showErrorDialog('NovelForge — Setup Failed', `Could not set up the application on first launch:\n\n${result.error}\n\n` +
                    'Please check your internet connection and make sure Git is installed.');
                return;
            }
        }
        createSplash();
        startEngine();
        try {
            await waitForEngine(ENGINE_PORT, 60000);
            console.log('[main] Engine ready on port', ENGINE_PORT);
        }
        catch (err) {
            splashWindow?.close();
            splashWindow = null;
            console.error('[main] Engine failed to start:', err);
            createMainWindow();
            return;
        }
    }
    createMainWindow();
});
electron_1.app.on('window-all-closed', () => { stopEngine(); if (process.platform !== 'darwin')
    electron_1.app.quit(); });
electron_1.app.on('activate', () => { if (!mainWindow)
    createMainWindow(); });
electron_1.app.on('before-quit', stopEngine);
