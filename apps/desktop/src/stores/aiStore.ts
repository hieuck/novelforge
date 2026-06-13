import { create } from 'zustand'
import { api } from '../lib/api'
import type { AIAction } from '../types'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}

interface AIMeta {
  projectId?: string | null
  chapterId?: string | null
  action?: AIAction
  instruction?: string
}

interface AIStore {
  messages: Message[]
  loading: boolean
  clearMessages: () => void
  addUserMessage: (text: string) => void
  addAssistantMessage: (text: string) => void
  /** HTTP fallback — also used to build history for WS sends */
  sendMessage: (text: string, meta?: AIMeta) => Promise<void>
  /** Returns the last N turn-pairs as history for the backend */
  getHistory: () => Array<{ role: string; content: string }>
}

function makeMsg(role: 'user' | 'assistant', content: string): Message {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    role,
    content,
    createdAt: new Date().toISOString(),
  }
}

const MAX_HISTORY_MSGS = 12 // 6 turns × 2

export const useAiStore = create<AIStore>((set, get) => ({
  messages: [],
  loading: false,

  clearMessages: () => set({ messages: [] }),

  addUserMessage: (text) =>
    set((s) => ({ messages: [...s.messages, makeMsg('user', text)] })),

  addAssistantMessage: (text) =>
    set((s) => ({ messages: [...s.messages, makeMsg('assistant', text)] })),

  /** Returns recent history excluding the most recent user message (which is sent as `text`). */
  getHistory: () => {
    const { messages } = get()
    // Take all but the last message (the current user turn hasn't been added yet)
    const prior = messages.slice(-MAX_HISTORY_MSGS)
    return prior.map((m) => ({ role: m.role, content: m.content }))
  },

  sendMessage: async (text, meta = {}) => {
    const history = get().getHistory()
    set((s) => ({ messages: [...s.messages, makeMsg('user', text)], loading: true }))
    try {
      const res = await api.post<{ result: string }>('/ai/run', {
        project_id: meta.projectId ?? null,
        chapter_id: meta.chapterId ?? null,
        action: meta.action ?? 'continue',
        text,
        instruction: meta.instruction ?? '',
        history,
      })
      set((s) => ({
        messages: [...s.messages, makeMsg('assistant', res.result ?? '[no response]')],
      }))
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Không kết nối được AI'
      set((s) => ({
        messages: [...s.messages, makeMsg('assistant', `Lỗi: ${msg}`)],
      }))
    } finally {
      set({ loading: false })
    }
  },
}))
