import { describe, it, expect, beforeAll, afterAll } from 'vitest'

const API = 'http://127.0.0.1:9000/api'

async function apiGet(path: string) {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`)
  return res.json()
}

async function apiPost(path: string, body: unknown) {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path}: ${res.status}`)
  return res.json()
}

async function apiDelete(path: string) {
  const res = await fetch(`${API}${path}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`DELETE ${path}: ${res.status}`)
}

describe('API Integration Tests', () => {
  let projectId: string

  it('health check', async () => {
    const data = await apiGet('/health')
    expect(data.status).toBe('ok')
  })

  it('creates a project', async () => {
    const data = await apiPost('/', { title: 'E2E Test Project', genre: 'Fantasy' })
    expect(data.title).toBe('E2E Test Project')
    expect(data.genre).toBe('Fantasy')
    expect(data.id).toBeTruthy()
    projectId = data.id
  })

  it('lists projects', async () => {
    const data = await apiGet('/')
    expect(Array.isArray(data)).toBe(true)
    expect(data.length).toBeGreaterThanOrEqual(1)
  })

  it('creates a chapter', async () => {
    const data = await apiPost('/', { project_id: projectId, title: 'Chapter 1', content: 'Once upon a time...' })
    expect(data.title).toBe('Chapter 1')
    expect(data.project_id).toBe(projectId)
  })

  it('deletes a project', async () => {
    await apiDelete(`/${projectId}`)
  })
})
