import { create } from 'zustand'

type Project = {
  id: string
  title: string
  description?: string
  genre?: string
  language?: string
  style_guide?: string
  summary?: string
  status?: string
  created_at?: string
  updated_at?: string
}

type ProjectStore = {
  projects: Project[]
  activeProjectId?: string
  setActiveProject: (id: string) => void
  fetchProjects: () => Promise<void>
  createProject: (values: Partial<Project>) => Promise<Project>
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  activeProjectId: undefined,
  setActiveProject: (id) => set({ activeProjectId: id }),
  fetchProjects: async () => {
    const res = await fetch('/api/projects')
    const data = await res.json()
    set({ projects: Array.isArray(data) ? data : [] })
  },
  createProject: async (values) => {
    const res = await fetch('/api/projects', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(values),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Create project failed')
    set((s) => ({ projects: [data, ...s.projects] }))
    return data
  },
}))
