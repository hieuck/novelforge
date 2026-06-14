import { test, expect } from '@playwright/test'

test.describe('User Journey', () => {
  test('full story creation flow', async ({ page }) => {
    // 1. Homepage loads
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('NovelForge')
    await expect(page.getByText('Dashboard')).toBeVisible()

    // 2. Create project
    page.on('dialog', async (dialog) => {
      expect(dialog.message()).toContain('tên project')
      await dialog.accept('Truyện ma')
    })
    await page.getByText('Tạo project mới').click()
    await page.waitForTimeout(1500)

    // Should navigate to chapters page
    await expect(page).toHaveURL(/\/projects\/.+\/chapters/)

    // 3. Create first chapter
    await page.getByText('Tạo chương đầu tiên').click()
    await page.waitForTimeout(1000)

    // 4. Write chapter content
    const textarea = page.locator('textarea[placeholder*="Bắt đầu viết"]')
    await expect(textarea).toBeVisible()
    await textarea.fill('Đêm tối. Tiếng gió rít bên ngoài. Linh ngồi trong góc phòng.')
    await page.waitForTimeout(2000) // wait for autosave

    // 5. Verify word count appears in status bar
    await expect(page.locator('span').filter({ hasText: /từ$/ }).first()).toBeVisible()

    // 6. Navigate to Characters
    await page.getByRole('link', { name: 'Characters' }).click()
    await page.waitForTimeout(1000)
    await expect(page.getByText('Character Bible')).toBeVisible()

    // 7. Create a character
    await page.getByText('Thêm nhân vật').click()
    const nameInput = page.locator('input[placeholder="Tên *"]')
    if (await nameInput.isVisible()) {
      await nameInput.fill('Linh')
      await page.getByText('Lưu nhân vật').click()
      await page.waitForTimeout(1000)
    }

    // 8. Navigate back to Dashboard
    await page.getByText('Dashboard').click()
    await page.waitForTimeout(1000)
    await expect(page.getByRole('heading', { name: /Projects/ })).toBeVisible()

    // 9. Verify project exists in list
    await expect(page.getByRole('button', { name: /Truyện ma/ }).first()).toBeVisible()
  })
})
