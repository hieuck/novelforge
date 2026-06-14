import { test, expect } from '@playwright/test'

test.describe('Full CRUD via API', () => {
  let pid: string

  test.beforeAll(async ({ request }) => {
    const r = await request.post('/api/projects/', {
      data: { title: 'E2E Full CRUD', genre: 'Fantasy' },
    })
    pid = (await r.json()).id
  })

  test.afterAll(async ({ request }) => {
    if (pid) await request.delete(`/api/projects/${pid}`)
  })

  test('create and get chapter', async ({ request }) => {
    const ch = await request.post('/api/chapters/', {
      data: { project_id: pid, title: 'Chapter 1', content: 'Once upon a time...' },
    })
    expect(ch.status()).toBe(201)
    const chData = await ch.json()
    expect(chData.project_id).toBe(pid)

    const get = await request.get(`/api/chapters/${chData.id}`)
    expect(get.status()).toBe(200)
  })

  test('create and get character', async ({ request }) => {
    const ch = await request.post('/api/characters/', {
      data: { project_id: pid, name: 'Hero', role: 'main', gender: 'Male' },
    })
    expect(ch.status()).toBe(201)
    const data = await ch.json()
    expect(data.name).toBe('Hero')
    expect(data.gender).toBe('Male')
  })

  test('create and get lore', async ({ request }) => {
    const lr = await request.post('/api/lore/', {
      data: { project_id: pid, lore_type: 'location', name: 'Enchanted Forest', tags: ['magic', 'forest'] },
    })
    expect(lr.status()).toBe(201)
    const data = await lr.json()
    expect(data.tags).toEqual(['magic', 'forest'])
  })

  test('create and get timeline event', async ({ request }) => {
    const tl = await request.post('/api/timeline/', {
      data: { project_id: pid, title: 'Hero departs', involved_characters: ['Hero'] },
    })
    expect(tl.status()).toBe(201)
  })

  test('list all sub-resources', async ({ request }) => {
    const ch = await request.get(`/api/projects/${pid}/chapters`)
    expect(ch.status()).toBe(200)
    expect((await ch.json()).length).toBeGreaterThanOrEqual(1)

    const chars = await request.get(`/api/projects/${pid}/characters`)
    expect(chars.status()).toBe(200)

    const lore = await request.get(`/api/projects/${pid}/lore`)
    expect(lore.status()).toBe(200)

    const tl = await request.get(`/api/projects/${pid}/timeline`)
    expect(tl.status()).toBe(200)

    const jobs = await request.get(`/api/projects/${pid}/jobs`)
    expect(jobs.status()).toBe(200)
  })

  test('search within project', async ({ request }) => {
    const r = await request.get(`/api/projects/${pid}/search?q=Once&limit=10`)
    expect(r.status()).toBe(200)
  })
})
