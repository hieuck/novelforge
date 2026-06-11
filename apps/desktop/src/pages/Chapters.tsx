import { useParams, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useChapterStore } from '../stores/chapterStore'

export default function Chapters() {
  const { projectId, chapterId } = useParams()
  const navigate = useNavigate()
  const { chapters, fetchChapters, createChapter } = useChapterStore()
  const active = chapterId || null

  useEffect(() => {
    if (!projectId) return
    fetchChapters(projectId)
  }, [projectId])

  const newChapter = async () => {
    if (!projectId) return
    const next = await createChapter({ project_id: projectId, title: 'Untitled', content: '', status: 'draft' })
    navigate(`/projects/${projectId}/chapters/${next.id}`)
  }

  return (
    <div className="flex h-full">
      <div className="w-64 border-r border-slate-800/70 bg-slate-900/60 p-3 text-sm">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">Chapters</span>
          <button onClick={newChapter} className="rounded bg-slate-800 px-2 py-1 text-xs">New</button>
        </div>
        <div className="space-y-1">
          {chapters.map((ch) => (
            <button
              key={ch.id}
              onClick={() => navigate(`/projects/${projectId}/chapters/${ch.id}`)}
              className={`block w-full rounded-md px-3 py-2 text-left ${ch.id === active ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:bg-slate-900'}`}
            >
              <div className="truncate">{ch.title || 'Untitled'}</div>
              <div className="text-[10px] text-slate-500">{ch.status || 'draft'}</div>
            </button>
          ))}
          {!chapters.length && <div className="text-xs text-slate-500">No chapters.</div>}
        </div>
      </div>
      <main className="flex-1 p-6 text-slate-500">{active ? 'Select or open a chapter.' : 'Create or select a chapter.'}</main>
    </div>
  )
}
