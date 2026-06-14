import { test, expect } from '@playwright/test'

test.describe.serial('Project CRUD via API', () => {
  let projectId: string

  test('create project', async ({ request }) => {
    const r = await request.post('/api/projects/', {
      data: { title: 'E2E Test Novel', genre: 'Fantasy', language: 'vi' },
    })
    expect(r.status()).toBe(201)
    const data = await r.json()
    expect(data.title).toBe('E2E Test Novel')
    expect(data.id).toBeTruthy()
    projectId = data.id
  })

  test('list + CRUD sub-resources', async ({ request }) => {
    // List projects
    const list = await request.get('/api/projects/')
    expect(list.status()).toBe(200)

    // Create chapter
    const ch = await request.post('/api/chapters/', {
      data: { project_id: projectId, title: 'Chapter 1', content: 'Story content...' },
    })
    expect(ch.status()).toBe(201)

    // Create character
    const chr = await request.post('/api/characters/', {
      data: { project_id: projectId, name: 'Hero', role: 'main' },
    })
    expect(chr.status()).toBe(201)

    // Create lore
    const lr = await request.post('/api/lore/', {
      data: { project_id: projectId, lore_type: 'location', name: 'Forest' },
    })
    expect(lr.status()).toBe(201)

    // Create timeline event
    const tl = await request.post('/api/timeline/', {
      data: { project_id: projectId, title: 'Hero begins journey' },
    })
    expect(tl.status()).toBe(201)

    // Search
    const search = await request.get(`/api/projects/${projectId}/search?q=content&limit=10`)
    expect(search.status()).toBe(200)
  })

  test('delete project', async ({ request }) => {
    const r = await request.delete(`/api/projects/${projectId}`)
    expect(r.status()).toBe(204)
  })
})

