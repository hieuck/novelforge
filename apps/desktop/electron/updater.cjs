const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const {
  AGENT_ROOT, NOVELFORGE_HOME, DESKTOP_STAMP,
  getInstallStamp,
} = require('./backend-probes.cjs');

const DEFAULT_BRANCH = 'main';

async function checkUpdates(branch = DEFAULT_BRANCH) {
  try {
    const stamp = getInstallStamp();
    if (!stamp || !stamp.pinnedCommit) {
      return { supported: false, reason: 'Not a git-based install' };
    }

    const remoteRef = await gitLsRemote(branch);
    if (!remoteRef) {
      return { supported: false, reason: 'Cannot reach remote' };
    }

    const currentSha = stamp.pinnedCommit;
    const remoteSha = remoteRef.trim().split(/\s+/)[0];

    if (currentSha === remoteSha) {
      return { available: false, currentSha, remoteSha };
    }

    const behind = await countCommitsBehind(currentSha, remoteSha);
    return { available: true, currentSha, remoteSha, behind, branch };
  } catch (err) {
    return { supported: false, reason: err.message };
  }
}

function applyUpdates(branch = DEFAULT_BRANCH) {
  const scriptContent = getUpdaterScriptContent();
  if (!scriptContent) {
    throw new Error('Updater script not found');
  }

  const scriptPath = path.join(NOVELFORGE_HOME, 'update-novelforge.ps1');
  fs.writeFileSync(scriptPath, scriptContent, 'utf-8');

  const powershellPath = path.join(
    process.env.SystemRoot || 'C:\\Windows',
    'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe'
  );
  const logFile = path.join(NOVELFORGE_HOME, 'logs', 'update.log');

  const proc = spawn(powershellPath, [
    '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', scriptPath,
    '-AgentRoot', AGENT_ROOT,
    '-VenvRoot', path.join(NOVELFORGE_HOME, 'venv'),
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

function getUpdaterScriptPath() {
  const devPath = path.join(__dirname, '..', 'scripts', 'update-novelforge.ps1');
  if (fs.existsSync(devPath)) return devPath;

  // Production: check resources/scripts (unpacked from asar)
  const prodPath = path.join(process.resourcesPath, 'scripts', 'update-novelforge.ps1');
  if (fs.existsSync(prodPath)) return prodPath;

  return null;
}

function getUpdaterScriptContent() {
  const scriptPath = getUpdaterScriptPath();
  if (scriptPath) {
    return fs.readFileSync(scriptPath, 'utf-8');
  }
  return null;
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
      if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
        hash.update(f);
        hash.update(fs.readFileSync(fullPath));
      }
    }
  } catch { return null; }
  return hash.digest('hex');
}

module.exports = {
  checkUpdates, applyUpdates,
  readDesktopStamp, writeDesktopStamp, computeDesktopContentHash,
};
