// Local desktop dev launcher kept for compatibility.
import { spawn } from 'child_process';
import { fileURLToPath, URL } from 'url';

const repo = process.cwd();
spawn('python', ['scripts/dev.py'], {
  cwd: repo,
  stdio: 'inherit',
  shell: true,
});
