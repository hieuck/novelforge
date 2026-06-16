import { describe, it, expect, vi } from 'vitest'
import { wsUrl, safeReq, api } from '@/lib/api'

describe('wsUrl', () => {
  it('default port', () => { delete (window as any).__NOVELFORGE__; const u = wsUrl('/ws/ai'); expect(u).toContain('9000'); expect(u).toContain('/api/ws/ai') })
  it('injected port', () => { ;(window as any).__NOVELFORGE__ = { enginePort: 8888 }; expect(wsUrl('/ws/x')).toContain('8888'); delete (window as any).__NOVELFORGE__ })
})

describe('safeReq', () => {
  it('returns result on success', async () => {
    const result = await safeReq('test', () => Promise.resolve(42))
    expect(result).toBe(42)
  })

  it('returns null and notifies on error', async () => {
    const fn = () => Promise.reject(new Error('boom'))
    const result = await safeReq('label', fn)
    expect(result).toBeNull()
  })
})

describe('api.get', () => {
  it('rejects on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 400, json: () => Promise.resolve({ detail: 'Bad' }) })
    await expect(api.get('/test')).rejects.toThrow('Bad')
  })

  it('returns json on ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve({ data: 1 }) })
    const result = await api.get('/test')
    expect(result).toEqual({ data: 1 })
  })
})
