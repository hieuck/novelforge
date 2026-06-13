import { create } from 'zustand'
import { api } from '../lib/api'
import type { Chapter } from '../types'

interface ChapterStore {
  chapters: Chapter[]
  activeChapterId?: string
  setActiveChapter: (id?: string) => void
  fetchChapters: (projectId: string) => Promise<void>
  createChapter: (values: Partial<Chapter>) => Promise<Chapter>
  updateChapter: (id: string, values: Partial<Chapter>) => Promise<void>
  deleteChapter: (id: string) => Promise<void>
}

export const useChapterStore = create<ChapterStore>((set, get) => ({
  chapters: [],
  activeChapterId: undefined,

  setActiveChapter: (id) => set({ activeChapterId: id }),

  fetchChapters: async (projectId) => {
    const data = await api.get<Chapter[]>(`/projects/${projectId}/chapters`)
    set({ chapters: Array.isArray(data) ? data : [] })
  },

  createChapter: async (values) => {
    const data = await api.post<Chapter>('/chapters/', values)
    set((s) => ({ chapters: [...s.chapters, data] }))
    return data
  },

  updateChapter: async (id, values) => {
    const data = await api.patch<Chapter>(`/chapters/${id}`, values)
    set((s) => ({
      chapters: s.chapters.map((c) => (c.id === id ? { ...c, ...data } : c)),
    }))
  },

  deleteChapter: async (id) => {
    await api.delete(`/chapters/${id}`)
    set((s) => ({
      chapters: s.chapters.filter((c) => c.id !== id),
      activeChapterId: get().activeChapterId === id ? undefined : get().activeChapterId,
    }))
  },
}))
