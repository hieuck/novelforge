import { defineConfig } from '@playwright/test'
import { execSync } from 'child_process'
import path from 'path'
import fs from 'fs'

function findPython(root: string): string {
  const candidates = [
    path.join(root, 'apps', 'engine', '.venv', 'Scripts', 'python.exe'),
    path.join(root, 'apps', 'engine', '.venv', 'bin', 'python3'),
  ]
  for (const c of candidates) {
    if (fs.existsSync(c)) return c
  }
  return 'python3'
}

const root = path.resolve(__dirname, '..', '..')
const python = findPython(root)
const isWin = process.platform === 'win32'

export default defineConfig({
  testDir: '.',
  testIgnore: ['api.test.ts'],
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
  },
  webServer: [
    {
      command: isWin
        ? `start /B ${python} scripts\\dev.py`
        : `${python} scripts/dev.py &`,
      port: 5173,
      cwd: root,
      timeout: 45000,
      reuseExistingServer: true,
      env: { PYTHONUNBUFFERED: '1' },
    },
  ],
})
