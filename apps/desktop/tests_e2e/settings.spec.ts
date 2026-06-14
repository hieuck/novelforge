import { test, expect } from '@playwright/test'

test.describe('Settings page', () => {
  test('settings page loads with tabs', async ({ page }) => {
    await page.goto('/#/settings')
    await page.waitForTimeout(1000)
    await expect(page.getByRole('button', { name: 'AI Provider' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'About' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Danger Zone' })).toBeVisible()
  })

  test('about tab shows engine info', async ({ page }) => {
    await page.goto('/#/settings')
    await page.waitForTimeout(1000)
    await page.getByRole('button', { name: 'About' }).click()
    await page.waitForTimeout(2000)
    await expect(page.getByRole('main').getByText('NovelForge').first()).toBeVisible()
  })

  test('danger zone shows confirmation input', async ({ page }) => {
    await page.goto('/#/settings')
    await page.waitForTimeout(1000)
    await page.getByRole('button', { name: 'Danger Zone' }).click()
    await page.waitForTimeout(500)
    await expect(page.getByPlaceholder('DELETE ALL')).toBeVisible()
  })
})
