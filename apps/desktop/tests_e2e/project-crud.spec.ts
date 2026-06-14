import { test, expect } from '@playwright/test'

test.describe('Project CRUD', () => {
  test('create and delete project via API', async ({ request }) => {
    const r = await request.post('/api/projects/', {
      data: { title: 'E2E API Test', genre: 'Fantasy' },
    })
    expect(r.status()).toBe(201)
    const data = await r.json()
    expect(data.id).toBeTruthy()
    expect(data.title).toBe('E2E API Test')

    const list = await request.get('/api/projects/')
    expect(list.status()).toBe(200)
    const projects = await list.json()
    expect(projects.some((p: any) => p.id === data.id)).toBe(true)

    const del = await request.delete(`/api/projects/${data.id}`)
    expect(del.status()).toBe(204)
  })
})
