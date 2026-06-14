const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const { AGENT_ROOT, VENV_ROOT, NOVELFORGE_HOME, BOOTSTRAP_MARKER, DESKTOP_STAMP } = require('./backend-probes.cjs');

const REPO_URL = 'https://github.com/hieuck/novelforge';
const BRANCH = 'main';

async function runBootstrap(onEvent) {
  const emit = (type, data) => {
    const ev = { type, data, timestamp: new Date().toISOString() };
    if (onEvent) onEvent(ev);
  };

  try {
    fs.mkdirSync(NOVELFORGE_HOME, { recursive: true });
    fs.mkdirSync(path.join(NOVELFORGE_HOME, 'logs'), { recursive: true });

    // 1. Git clone
    emit('stage', { name: 'clone', message: 'Cloning repository...' });
    await runCommand('git', ['clone', '--depth', '1', '--branch', BRANCH, REPO_URL, AGENT_ROOT], { emit });

    // 2. Create venv
    emit('stage', { name: 'venv', message: 'Creating Python virtual environment...' });
    await runCommand('uv', ['venv', VENV_ROOT], { emit });

    // 3. Install deps
    emit('stage', { name: 'deps', message: 'Installing Python dependencies...' });
    const pythonExe = process.platform === 'win32'
      ? path.join(VENV_ROOT, 'Scripts', 'python.exe')
      : path.join(VENV_ROOT, 'bin', 'python');
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
      env: { ...process.env },
    });
    let stdout = '';
    proc.stdout.on('data', (d) => {
      const s = d.toString();
      stdout += s;
      if (emit) emit('log', s.trim());
    });
    proc.stderr.on('data', (d) => {
      if (emit) emit('log', d.toString().trim());
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
    let out = '';
    proc.stdout.on('data', (d) => { out += d.toString(); });
    proc.on('close', (code) => {
      if (code === 0) resolve(out.trim());
      else reject(new Error(`git rev-parse failed (exit ${code})`));
    });
    proc.on('error', reject);
  });
}

async function computeContentHash(dir) {
  const hash = crypto.createHash('sha256');
  const files = await getSourceFiles(dir);
  for (const f of files.sort()) {
    const fullPath = path.join(dir, f);
    if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
      hash.update(f);
      hash.update(fs.readFileSync(fullPath));
    }
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
