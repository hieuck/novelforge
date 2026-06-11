import { create } from 'zustand'

export type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}

export type AIState = {
  messages: Message[]
  loading: boolean
  sendMessage: (text: string, meta?: { projectId?: string; chapterId?: string; action?: string }) => Promise<void>
}

export const useAiStore = create<AIState>((set, _get) => ({
  messages: [],
  loading: false,
  sendMessage: async (text, meta) => {
    const next: Message = {
      id: String(Date.now()),
      role: 'user',
      content: text,
      createdAt: new Date().toISOString(),
    }
    set((s) => ({ messages: [...s.messages, next], loading: true }))
    try {
      const res = await fetch('/api/ai/run', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          project_id: meta?.projectId,
          chapter_id: meta?.chapterId,
          action: meta?.action || 'continue',
          text,
          instruction: '',
        }),
      }),
        data = await res.json()
        const reply: Message = {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: data.result || data.detail || '[no response]',
          createdAt: new Date().toISOString(),
        }
        set((s) => ({ messages: [...s.messages, reply] }))
    } catch (e) {
      set((s) => ({
        messages: [
          ...s.messages,
          {
            id: String(Date.now() + 2),
            role: 'assistant',
            content: 'Không thể kết nối AI.',
            createdAt: new Date().toISOString(),
          },
        ],
      }))
    } finally {
      set({ loading: false })
    }
  },
}))
