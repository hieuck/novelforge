import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useChapterStore } from '@/stores/chapterStore'
const c1 = { id: 'c1', project_id: 'p1', title: 'Ch1', content: 'hello world', status: 'draft', scene_order: 0, word_count: 2 }
const c2 = { id: 'c2', project_id: 'p1', title: 'Ch2', content: 'foo', status: 'draft', scene_order: 1, word_count: 1 }
global.fetch = vi.fn()
function mf(d: unknown, st = 200) { (global.fetch as any).mockResolvedValueOnce({ ok: st < 400, status: st, json: async () => d }) }
describe('chapterStore', () => {
  beforeEach(() => { vi.clearAllMocks(); useChapterStore.setState({ chapters: [], activeChapterId: undefined }) })
  it('fetch', async () => { mf([c1,c2]); await useChapterStore.getState().fetchChapters('p1'); expect(useChapterStore.getState().chapters).toHaveLength(2) })
  it('create', async () => { mf(c1); const ch = await useChapterStore.getState().createChapter({project_id:'p1',title:'Ch1'}); expect(ch.id).toBe('c1') })
  it('update', async () => { useChapterStore.setState({chapters:[c1]}); mf({...c1,title:'New'}); await useChapterStore.getState().updateChapter('c1',{title:'New'}); expect(useChapterStore.getState().chapters[0].title).toBe('New') })
  it('delete', async () => { useChapterStore.setState({chapters:[c1,c2]}); mf(undefined,204); await useChapterStore.getState().deleteChapter('c1'); expect(useChapterStore.getState().chapters).toHaveLength(1) })
  it('delete active clears', async () => { useChapterStore.setState({chapters:[c1],activeChapterId:'c1'}); mf(undefined,204); await useChapterStore.getState().deleteChapter('c1'); expect(useChapterStore.getState().activeChapterId).toBeUndefined() })
  it('setActive', () => { useChapterStore.getState().setActiveChapter('c1'); expect(useChapterStore.getState().activeChapterId).toBe('c1') })
})
