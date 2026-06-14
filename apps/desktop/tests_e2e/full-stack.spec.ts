import { test, expect } from '@playwright/test'

test.describe('Full stack E2E', () => {
  let projectId: string

  test('create project with UI', async ({ page }) => {
    await page.goto('/')

    // Verify homepage
    await expect(page.locator('h1')).toContainText('NovelForge')

    // Handle dialog and click create
    page.once('dialog', async (d) => {
      await d.accept('Playwright Full Story')
    })
    await page.getByText('Tạo project mới').click()
    await page.waitForTimeout(2000)

    // Should be on chapters page
    await expect(page).toHaveURL(/\/projects\//)
  })

  test('verify project via API', async ({ request }) => {
    const r = await request.get('/api/projects/')
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(Array.isArray(data)).toBe(true)
    if (data.length > 0) {
      projectId = data[0].id
    }
  })

  test('check engine health', async ({ request }) => {
    const r = await request.get('/api/health')
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data.status).toBe('ok')
  })

  test('settings page renders', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByText('AI Provider')).toBeVisible()
    await expect(page.getByText('About')).toBeVisible()
  })
})
