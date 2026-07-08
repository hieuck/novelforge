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

function findRepoRoot(start: string): string {
  let dir = start
  while (dir !== path.dirname(dir)) {
    const pkg = path.join(dir, 'package.json')
    if (fs.existsSync(pkg)) {
      try {
        const content = JSON.parse(fs.readFileSync(pkg, 'utf-8'))
        if (Array.isArray(content.workspaces)) return dir
      } catch {
        // ignore malformed package.json
      }
    }
    dir = path.dirname(dir)
  }
  return path.resolve(__dirname, '..', '..', '..')
}

const root = findRepoRoot(__dirname)
const python = findPython(root)
const isWin = process.platform === 'win32'
const devScript = path.join(root, 'scripts', 'dev.py')

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
        ? `start /B ${python} "${devScript}"`
        : `${python} "${devScript}"`,
      port: 5173,
      cwd: root,
      timeout: 120000,
      reuseExistingServer: process.env.CI ? false : true,
      env: { PYTHONUNBUFFERED: '1' },
    },
  ],
})
