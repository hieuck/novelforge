import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useSettingsStore } from '@/stores/settingsStore'
global.fetch = vi.fn()
function mf(d: unknown, st = 200) { (global.fetch as any).mockResolvedValueOnce({ ok: st < 400, status: st, json: async () => d }) }
const D = { provider: 'ollama', base_url: 'http://localhost:11434', api_key: '', model: 'llama3.1:8b', temperature: 0.7, max_tokens: 2048 }
describe('settingsStore', () => {
  beforeEach(() => { vi.clearAllMocks(); useSettingsStore.setState({ settings: D, loaded: false }) })
  it('fetch ok', async () => { mf({...D, model: 'gemma3:4b'}); await useSettingsStore.getState().fetchSettings(); expect(useSettingsStore.getState().settings.model).toBe('gemma3:4b') })
  it('fetch error', async () => { (global.fetch as any).mockRejectedValueOnce(new Error('net')); await useSettingsStore.getState().fetchSettings(); expect(useSettingsStore.getState().loaded).toBe(true) })
  it('save', async () => { mf({...D, provider: 'openai_compat'}); const r = await useSettingsStore.getState().saveSettings({...D, provider: 'openai_compat'} as any); expect(r.ok).toBe(true) })
  it('save error', async () => { (global.fetch as any).mockRejectedValueOnce(new Error('fail')); const r = await useSettingsStore.getState().saveSettings(D as any); expect(r.ok).toBe(false) })
  it('test ok', async () => { mf({ok: true}); const r = await useSettingsStore.getState().testConnection(D as any); expect(r.ok).toBe(true) })
  it('test fail', async () => { mf({ok: false}); const r = await useSettingsStore.getState().testConnection(D as any); expect(r.ok).toBe(false) })
})
