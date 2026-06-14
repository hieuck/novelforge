import { test, expect } from '@playwright/test'

test.describe('Characters page', () => {
  test('characters page loads and shows empty state', async ({ page }) => {
    // First create a project via API
    const r = await page.request.post('/api/projects/', {
      data: { title: 'Character Test Story', genre: 'Fantasy' },
    })
    const pid = (await r.json()).id

    await page.goto(`/#/projects/${pid}/characters`)
    await page.waitForTimeout(2000)
    await expect(page.getByText('Character Bible')).toBeVisible()
  })

  test('create and verify a character via API', async ({ request }) => {
    const r = await request.post('/api/projects/', {
      data: { title: 'Character CRUD', genre: 'Fantasy' },
    })
    const pid = (await r.json()).id

    // Create character
    const ch = await request.post('/api/characters/', {
      data: {
        project_id: pid,
        name: 'Aria',
        gender: 'Nữ',
        role: 'Nhân vật chính',
        age: '22',
        personality: 'Dũng cảm, thông minh',
        goals: 'Tìm kiếm sự thật',
        secrets: 'Có nguồn gốc bí ẩn',
      },
    })
    expect(ch.status()).toBe(201)

    // List characters
    const list = await request.get(`/api/projects/${pid}/characters`)
    expect(list.status()).toBe(200)
    const data = await list.json()
    expect(data.length).toBeGreaterThanOrEqual(1)
    expect(data[0].name).toBe('Aria')
  })
})
