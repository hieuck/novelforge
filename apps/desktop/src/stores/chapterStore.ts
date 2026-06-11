import { create } from 'zustand'

type Chapter = {
  id: string
  project_id: string
  title: string
  content?: string
  word_count?: number
  status?: string
  scene_order?: number
  summary?: string
  notes?: string
  is_deleted?: boolean
  created_at?: string
  updated_at?: string
}

type ChapterStore = {
  chapters: Chapter[]
  activeChapterId?: string
  setActiveChapter: (id?: string) => void
  fetchChapters: (projectId: string) => Promise<void>
  createChapter: (values: Partial<Chapter>) => Promise<Chapter>
  updateChapter: (id: string, values: Partial<Chapter>) => Promise<void>
}

export const useChapterStore = create<ChapterStore>((set) => ({
  chapters: [],
  activeChapterId: undefined,
  setActiveChapter: (id) => set({ activeChapterId: id }),
  fetchChapters: async (projectId) => {
    const res = await fetch(`/api/projects/${projectId}/chapters`)
    const data = await res.json()
    set({ chapters: Array.isArray(data) ? data : [] })
  },
  createChapter: async (values) => {
    const res = await fetch('/api/chapters', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(values),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Create chapter failed')
    set((s) => ({ chapters: [data, ...s.chapters] }))
    return data
  },
  updateChapter: async (id, values) => {
    const res = await fetch(`/api/chapters/${id}`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(values),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Update chapter failed')
    set((s) => ({
      chapters: s.chapters.map((c) => (c.id === id ? { ...c, ...data } : c)),
    }))
  },
}))
