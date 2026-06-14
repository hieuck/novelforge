import { create } from 'zustand'
import { api } from '../lib/api'

interface ConnectionStore {
  connected: boolean
  checking: boolean
  lastCheck: number | null
  check: () => Promise<void>
}

export const useConnectionStore = create<ConnectionStore>((set) => ({
  connected: false,
  checking: false,
  lastCheck: null,

  check: async () => {
    set({ checking: true })
    try {
      await api.get('/health')
      set({ connected: true, checking: false, lastCheck: Date.now() })
    } catch {
      set({ connected: false, checking: false, lastCheck: Date.now() })
    }
  },
}))
