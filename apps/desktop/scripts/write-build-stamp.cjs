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
