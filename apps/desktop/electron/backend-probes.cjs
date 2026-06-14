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

  // 4. Bootstrap needed
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
  } catch {
    return null;
  }
}

function validateAgentRoot(root) {
  return fs.existsSync(path.join(root, 'apps', 'engine'));
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
