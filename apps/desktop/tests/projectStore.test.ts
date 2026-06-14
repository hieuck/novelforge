import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useProjectStore } from '@/stores/projectStore'
const p1 = { id: 'p1', title: 'Novel', genre: 'Fantasy', language: 'vi', created_at: '', updated_at: '' }
const p2 = { id: 'p2', title: 'SciFi', genre: 'SciFi', language: 'en', created_at: '', updated_at: '' }
global.fetch = vi.fn()
function mf(d: unknown, st = 200) { (global.fetch as any).mockResolvedValueOnce({ ok: st < 400, status: st, json: async () => d }) }
describe('projectStore', () => {
  beforeEach(() => { vi.clearAllMocks(); useProjectStore.setState({ projects: [], activeProjectId: undefined }) })
  it('fetch', async () => { mf([p1,p2]); await useProjectStore.getState().fetchProjects(); expect(useProjectStore.getState().projects).toHaveLength(2) })
  it('fetch empty', async () => { mf([]); await useProjectStore.getState().fetchProjects(); expect(useProjectStore.getState().projects).toHaveLength(0) })
  it('create', async () => { mf(p1); await useProjectStore.getState().createProject({title:'N'}); expect(useProjectStore.getState().projects).toHaveLength(1) })
  it('create prepends', async () => { useProjectStore.setState({projects:[p2]}); mf(p1); await useProjectStore.getState().createProject({title:'N'}); expect(useProjectStore.getState().projects[0].id).toBe('p1') })
  it('update', async () => { useProjectStore.setState({projects:[p1]}); mf({...p1,title:'X'}); await useProjectStore.getState().updateProject('p1',{title:'X'}); expect(useProjectStore.getState().projects[0].title).toBe('X') })
  it('delete', async () => { useProjectStore.setState({projects:[p1,p2]}); mf(undefined,204); await useProjectStore.getState().deleteProject('p1'); expect(useProjectStore.getState().projects).toHaveLength(1) })
  it('setActive', () => { useProjectStore.getState().setActiveProject('p1'); expect(useProjectStore.getState().activeProjectId).toBe('p1') })
})
