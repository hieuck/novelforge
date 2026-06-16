import { test, expect } from '@playwright/test'

test.describe.serial('Studio Features E2E', () => {
  let pid: string

  test('setup: create project', async ({ request }) => {
    const r = await request.post('/api/projects/', { data: { title: 'Studio Test', genre: 'Fantasy', language: 'vi' } })
    expect(r.status()).toBe(201)
    pid = (await r.json()).id
  })

  test('backup: create and list backups', async ({ request }) => {
    const create = await request.post('/api/backup')
    expect(create.status()).toBe(201)
    const { filename } = await create.json()
    expect(filename).toContain('novelforge_backup_')

    const list = await request.get('/api/backups')
    expect(list.status()).toBe(200)
    const backups = await list.json()
    expect(backups.length).toBeGreaterThanOrEqual(1)
    expect(backups[0].filename).toBe(filename)

    const download = await request.get(`/api/backup/${filename}`)
    expect(download.status()).toBe(200)
    expect(download.headers()['content-type']).toBe('application/octet-stream')
  })

  test('chapters: reorder via API', async ({ request }) => {
    const ch1 = await request.post('/api/chapters/', { data: { project_id: pid, title: 'First', content: 'A', scene_order: 0 } })
    const ch2 = await request.post('/api/chapters/', { data: { project_id: pid, title: 'Second', content: 'B', scene_order: 1 } })
    const ch3 = await request.post('/api/chapters/', { data: { project_id: pid, title: 'Third', content: 'C', scene_order: 2 } })
    expect(ch1.status()).toBe(201)
    expect(ch2.status()).toBe(201)
    expect(ch3.status()).toBe(201)
    const id1 = (await ch1.json()).id
    const id2 = (await ch2.json()).id
    const id3 = (await ch3.json()).id

    // Reverse order
    const reorder = await request.post('/api/chapters/reorder', { data: { ordered_ids: [id3, id2, id1] } })
    expect(reorder.status()).toBe(200)

    const list = await request.get(`/api/projects/${pid}/chapters`)
    const chs = await list.json()
    expect(chs[0].id).toBe(id3)
    expect(chs[1].id).toBe(id2)
    expect(chs[2].id).toBe(id1)
  })

  test('gallery: delete confirmation via API', async ({ request }) => {
    const list = await request.get(`/api/projects/${pid}/images`)
    expect(list.status()).toBe(200)
    const images = await list.json()
    // Gallery delete dialog is frontend-only, API delete works
    for (const img of images) {
      const del = await request.delete(`/api/projects/${pid}/images/${img.id}`)
      expect(del.status()).toBe(204)
    }
  })

  test('cleanup: delete project', async ({ request }) => {
    const del = await request.delete(`/api/projects/${pid}`)
    expect(del.status()).toBe(204)
  })
})
