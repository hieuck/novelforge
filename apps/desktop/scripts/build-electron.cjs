const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 1. Compile TypeScript
execSync('npx tsc -p tsconfig.electron.json', { stdio: 'inherit', cwd: __dirname + '/..' });

// 2. Create CJS wrapper for ESM compatibility (package.json has "type": "module")
//    When loaded from a .cjs file, Node.js uses CommonJS loader for require() targets,
//    bypassing the "type": "module" setting that would otherwise break our require/exports usage.
fs.writeFileSync(path.join(__dirname, '..', 'dist-electron', 'main.cjs'),
  'require("./main.js");'
);

// 3. Write build stamp
const stamp = {
  schemaVersion: 1,
  commit: (() => { try { return execSync('git rev-parse HEAD', { encoding: 'utf8', cwd: __dirname + '/../..' }).trim(); } catch { return 'unknown'; } })(),
  branch: (() => { try { return execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8', cwd: __dirname + '/../..' }).trim(); } catch { return 'unknown'; } })(),
  builtAt: new Date().toISOString(),
  dirty: (() => { try { return execSync('git status --porcelain', { encoding: 'utf8', cwd: __dirname + '/../..' }).length > 0; } catch { return true; } })(),
  source: 'git',
};
fs.writeFileSync(path.join(__dirname, '..', 'dist-electron', 'install-stamp.json'), JSON.stringify(stamp, null, 2));
console.log('Build stamp:', JSON.stringify(stamp, null, 2));
