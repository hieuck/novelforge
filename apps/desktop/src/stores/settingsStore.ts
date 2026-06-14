import { create } from 'zustand'
import { api } from '../lib/api'
import type { AISettings } from '../types'

interface SettingsStore {
  settings: AISettings
  loaded: boolean
  fetchSettings: () => Promise<void>
  saveSettings: (values: AISettings) => Promise<{ ok: boolean; error?: string }>
  testConnection: (values: AISettings) => Promise<{ ok: boolean; response?: string; error?: string }>
}

const defaults: AISettings = {
  provider: 'ollama',
  base_url: 'http://localhost:11434',
  api_key: '',
  model: 'llama3.1:8b',
  temperature: 0.7,
  max_tokens: 2048,
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: defaults,
  loaded: false,

  fetchSettings: async () => {
    try {
      const data = await api.get<AISettings>('/settings/current')
      set({ settings: { ...defaults, ...data }, loaded: true })
    } catch {
      set({ loaded: true })
    }
  },

  saveSettings: async (values) => {
    try {
      const data = await api.post<AISettings>('/settings/current', values)
      set({ settings: { ...defaults, ...data } })
      return { ok: true }
    } catch (e: any) {
      return { ok: false, error: e.message }
    }
  },

  testConnection: async (values) => {
    try {
      const data = await api.post<{ ok: boolean; response?: string; error?: string }>(
        '/settings/test', values
      )
      return data
    } catch (e: any) {
      return { ok: false, error: e.message }
    }
  },
}))
