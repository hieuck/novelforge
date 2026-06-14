import { test, expect } from '@playwright/test'

test.describe('NovelForge UI', () => {
  test('homepage loads and shows title', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('NovelForge')
  })

  test('sidebar navigation is visible', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('Settings')).toBeVisible()
  })

  test('engine health via proxy', async ({ page }) => {
    const resp = await page.request.get('/api/health')
    expect(resp.status()).toBe(200)
    const data = await resp.json()
    expect(data.status).toBe('ok')
  })
})
