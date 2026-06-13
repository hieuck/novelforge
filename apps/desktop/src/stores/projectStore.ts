import { create } from 'zustand'
import { api } from '../lib/api'
import type { Project } from '../types'

interface ProjectStore {
  projects: Project[]
  activeProjectId?: string
  setActiveProject: (id: string) => void
  fetchProjects: () => Promise<void>
  createProject: (values: Partial<Project>) => Promise<Project>
  updateProject: (id: string, values: Partial<Project>) => Promise<Project>
  deleteProject: (id: string) => Promise<void>
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  activeProjectId: undefined,

  setActiveProject: (id) => set({ activeProjectId: id }),

  fetchProjects: async () => {
    const data = await api.get<Project[]>('/projects/')
    set({ projects: Array.isArray(data) ? data : [] })
  },

  createProject: async (values) => {
    const data = await api.post<Project>('/projects/', values)
    set((s) => ({ projects: [data, ...s.projects] }))
    return data
  },

  updateProject: async (id, values) => {
    const data = await api.patch<Project>(`/projects/${id}`, values)
    set((s) => ({ projects: s.projects.map((p) => (p.id === id ? data : p)) }))
    return data
  },

  deleteProject: async (id) => {
    await api.delete(`/projects/${id}`)
    set((s) => ({ projects: s.projects.filter((p) => p.id !== id) }))
  },
}))
