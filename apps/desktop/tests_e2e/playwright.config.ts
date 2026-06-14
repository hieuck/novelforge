import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
  },
  webServer: [
    {
      command: 'python ../../scripts/dev.py',
      port: 5173,
      cwd: '../..',
      timeout: 30000,
      reuseExistingServer: true,
    },
  ],
})
