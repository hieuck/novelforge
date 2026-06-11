import { create } from 'zustand'

export type Settings = {
  provider: string
  base_url: string
  api_key: string
  model: string
  temperature: string
  max_tokens: string
}

const defaultSettings: Settings = {
  provider: 'ollama',
  base_url: 'http://localhost:11434',
  api_key: '',
  model: 'llama3.1:8b',
  temperature: '0.7',
  max_tokens: '2048',
}

type SettingsStore = {
  settings: Settings
  updateSettings: (values: Partial<Settings>) => void
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: defaultSettings,
  updateSettings: (values) =>
    set((s) => ({
      settings: { ...s.settings, ...values },
    })),
}))
