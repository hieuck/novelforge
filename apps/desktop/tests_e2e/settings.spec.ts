import { test, expect } from '@playwright/test'

test.describe('Settings page', () => {
  test('settings page loads with tabs', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByText('AI Provider')).toBeVisible()
    await expect(page.getByText('About')).toBeVisible()
    await expect(page.getByText('Danger Zone')).toBeVisible()
  })

  test('about tab loads with engine info', async ({ page }) => {
    await page.goto('/settings')
    await page.getByText('About').click()
    await page.waitForTimeout(2000)
    await expect(page.getByText('NovelForge')).toBeVisible()
  })

  test('danger zone shows confirmation input', async ({ page }) => {
    await page.goto('/settings')
    await page.getByText('Danger Zone').click()
    await page.waitForTimeout(500)
    await expect(page.getByPlaceholder('DELETE ALL')).toBeVisible()
  })
})
