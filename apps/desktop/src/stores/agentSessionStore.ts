import { create } from 'zustand'

interface AgentSession {
  projectId: string | null
  chapterId: string | null
  chapterTitle: string | null
  task: string
  status: 'idle' | 'planning' | 'running' | 'asking' | 'done' | 'cancelled' | 'error'
  panelOpen: boolean
}

interface AgentSessionStore {
  session: AgentSession
  start: (projectId: string | null, chapterId?: string, chapterTitle?: string) => void
  setStatus: (status: AgentSession['status']) => void
  setTask: (task: string) => void
  setPanelOpen: (open: boolean) => void
  reset: () => void
}

const defaults: AgentSession = {
  projectId: null,
  chapterId: null,
  chapterTitle: null,
  task: '',
  status: 'idle',
  panelOpen: false,
}

export const useAgentSessionStore = create<AgentSessionStore>((set) => ({
  session: defaults,

  start: (projectId, chapterId, chapterTitle) =>
    set({ session: { ...defaults, projectId: projectId ?? null, chapterId: chapterId ?? null, chapterTitle: chapterTitle ?? null, status: 'idle', panelOpen: true } }),

  setStatus: (status) =>
    set((s) => ({ session: { ...s.session, status } })),

  setTask: (task) =>
    set((s) => ({ session: { ...s.session, task } })),

  setPanelOpen: (open) =>
    set((s) => ({ session: { ...s.session, panelOpen: open } })),

  reset: () => set({ session: defaults }),
}))
