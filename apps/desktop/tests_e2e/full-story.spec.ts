import { test, expect } from '@playwright/test'

test.describe.serial('Full Story E2E', () => {
  let projectId: string
  let chapter1Id: string
  let chapter2Id: string
  let charId: string
  let loreId: string
  let timelineId: string

  test('B1: Tạo project', async ({ request }) => {
    const r = await request.post('/api/projects/', {
      data: { title: 'Truyện Ma Rừng', genre: 'Horror', language: 'vi' },
    })
    expect(r.status()).toBe(201)
    projectId = (await r.json()).id
    console.log(`✅ Project: ${projectId}`)
  })

  test('B2: Tạo chapter 1', async ({ request }) => {
    const r = await request.post('/api/chapters/', {
      data: {
        project_id: projectId,
        title: 'Chương 1: Đêm',
        content: 'Trời tối. Tiếng gió rít qua kẽ lá. Linh đứng trước căn nhà hoang, tim đập nhanh. Cô biết có ai đó đang nhìn mình từ trong bóng tối.',
      },
    })
    expect(r.status()).toBe(201)
    const data = await r.json()
    chapter1Id = data.id
    expect(data.word_count).toBeGreaterThan(10)
    console.log(`✅ Chapter 1: ${chapter1Id} (${data.word_count} từ)`)
  })

  test('B3: Tạo chapter 2', async ({ request }) => {
    const r = await request.post('/api/chapters/', {
      data: {
        project_id: projectId,
        title: 'Chương 2: Bóng Ma',
        content: 'Cánh cửa từ từ mở ra. Một bóng trắng lướt qua hành lang. Linh rùng mình. Đó không phải là gió. Có thứ gì đó đang ở đây với cô.',
      },
    })
    expect(r.status()).toBe(201)
    const data = await r.json()
    chapter2Id = data.id
    console.log(`✅ Chapter 2: ${chapter2Id}`)
  })

  test('B4: Tạo nhân vật', async ({ request }) => {
    const r = await request.post('/api/characters/', {
      data: {
        project_id: projectId,
        name: 'Linh',
        gender: 'Nữ',
        role: 'Nhân vật chính',
        age: '22',
        personality: 'Dũng cảm, tò mò nhưng dễ bị ám ảnh',
        appearance: 'Tóc đen dài, mắt nâu, dáng người mảnh khảnh',
        goals: 'Tìm ra sự thật về căn nhà hoang',
        secrets: 'Từng có trải nghiệm siêu nhiên khi nhỏ',
      },
    })
    expect(r.status()).toBe(201)
    charId = (await r.json()).id
    console.log(`✅ Character: ${charId}`)
  })

  test('B5: Tạo lore', async ({ request }) => {
    const r = await request.post('/api/lore/', {
      data: {
        project_id: projectId,
        lore_type: 'location',
        name: 'Căn nhà hoang cuối làng',
        description: 'Một ngôi nhà bỏ hoang ở rìa làng, nơi đồn đại có ma. Chủ nhà cũ đã mất tích bí ẩn.',
        tags: ['nhà hoang', 'bí ẩn', 'ma quái'],
      },
    })
    expect(r.status()).toBe(201)
    loreId = (await r.json()).id
    console.log(`✅ Lore: ${loreId}`)
  })

  test('B6: Tạo timeline', async ({ request }) => {
    const r = await request.post('/api/timeline/', {
      data: {
        project_id: projectId,
        title: 'Linh vào nhà hoang',
        description: 'Đêm đầu tiên Linh bước vào căn nhà hoang.',
        involved_characters: [charId],
      },
    })
    expect(r.status()).toBe(201)
    timelineId = (await r.json()).id
    console.log(`✅ Timeline: ${timelineId}`)
  })

  test('B7: Đọc chapter và verify', async ({ request }) => {
    const r = await request.get(`/api/chapters/${chapter1Id}`)
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data.title).toBe('Chương 1: Đêm')
    expect(data.content).toContain('Linh')
  })

  test('B8: Sửa chapter', async ({ request }) => {
    const r = await request.patch(`/api/chapters/${chapter1Id}`, {
      data: { content: 'Trời tối. Tiếng gió rít qua kẽ lá. Linh đứng trước căn nhà hoang, tim đập nhanh. Một bóng đen lướt qua cửa sổ. Cô biết có ai đó đang nhìn mình từ trong bóng tối.' },
    })
    expect(r.status()).toBe(200)
    expect((await r.json()).word_count).toBeGreaterThan(15)
  })

  test('B9: Export MD', async ({ request }) => {
    const r = await request.post('/api/export', {
      data: { project_id: projectId, fmt: 'md' },
    })
    expect(r.status()).toBe(200)
  })

  test('B10: Export HTML', async ({ request }) => {
    const r = await request.post('/api/export', {
      data: { project_id: projectId, fmt: 'html' },
    })
    expect(r.status()).toBe(200)
  })

  test('B11: Search trong project', async ({ request }) => {
    const r = await request.get(`/api/projects/${projectId}/search?q=Linh&limit=10`)
    expect(r.status()).toBe(200)
  })

  test('B12: Settings about', async ({ request }) => {
    const r = await request.get('/api/settings/about')
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data.app).toBe('NovelForge')
  })

  test('B13: Xóa project (cascade)', async ({ request }) => {
    const del = await request.delete(`/api/projects/${projectId}`)
    expect(del.status()).toBe(204)

    const check = await request.get(`/api/projects/${projectId}`)
    expect(check.status()).toBe(404)
    console.log(`✅ Project deleted, cascade OK`)
  })
})
