import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useChapterStore } from '../stores/chapterStore'
import { useProjectStore } from '../stores/projectStore'

export default function Editor() {
  const { projectId, chapterId } = useParams()
  const { chapters, activeChapterId, setActiveChapter, updateChapter } = useChapterStore()
  const currentId = chapterId || activeChapterId
  const chapter = chapters.find((c) => c.id === currentId)
  const [text, setText] = useState(chapter?.content || '')
  const [title, setTitle] = useState(chapter?.title || '')
  const [status, setStatus] = useState(chapter?.status || 'draft')

  useEffect(() => {
    if (!projectId) return
    useProjectStore.getState().fetchProjects()
    useChapterStore.getState().fetchChapters(projectId)
  }, [projectId])

  useEffect(() => {
    setText(chapter?.content || '')
    setTitle(chapter?.title || '')
    setStatus(chapter?.status || 'draft')
  }, [chapter?.id, chapters])

  const save = async () => {
    if (!currentId) return
    await updateChapter(currentId, { content: text, title, status })
  }

  return (
    <div className="flex h-full">
      <div className="w-64 border-r border-slate-800/70 bg-slate-900/60 p-3 space-y-2 overflow-y-auto text-sm">
        <div className="px-2 py-1.5 text-xs font-semibold text-slate-300">Chapters</div>
        {chapters.map((ch) => (
          <button
            key={ch.id}
            onClick={() => {
              setActiveChapter(ch.id)
              window.location.hash = `/projects/${projectId}/chapters/${ch.id}`
            }}
            className={`block w-full rounded-md px-3 py-2 text-left transition-colors ${
              ch.id === currentId ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:bg-slate-900'
            }`}
          >
            <div className="truncate">{ch.title || 'Untitled'}</div>
            <div className="text-xs text-slate-500">{ch.status || 'draft'}</div>
          </button>
        ))}
      </div>
      <div className="flex flex-[3] flex-col border-r border-slate-800/70">
        <div className="flex items-center gap-3 border-b border-slate-800/70 px-4 py-2">
          <input
            className="flex-1 bg-transparent text-lg font-semibold outline-none"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Chapter title"
          />
          <select
            className="rounded-md border border-slate-800 bg-slate-900 px-2 py-1 text-xs"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="draft">Draft</option>
            <option value="revised">Revised</option>
            <option value="final">Final</option>
          </select>
          <button onClick={save} className="rounded-md bg-slate-800 px-3 py-2 text-xs text-slate-100">
            Save
          </button>
        </div>
        <textarea
          className="flex-1 resize-none bg-transparent p-4 font-mono leading-relaxed outline-none"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Start writing..."
        />
        <div className="flex items-center justify-between border-t border-slate-800/70 px-4 py-2 text-xs text-slate-400">
          <span>{text.split(/\s+/).filter(Boolean).length} words</span>
          <span>Saved manually</span>
        </div>
      </div>
    </div>
  )
}
