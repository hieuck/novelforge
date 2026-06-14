import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Plus, Trash2, CheckCircle, Save, Loader2,
  FileText, Bot,
} from 'lucide-react'
import { useChapterStore } from '../stores/chapterStore'
import AgentPanel from '../components/AgentPanel'
import type { Chapter } from '../types'

const STATUS_OPTIONS = ['draft', 'revised', 'final'] as const
const STATUS_COLOR: Record<string, string> = {
  draft:   'text-slate-500',
  revised: 'text-yellow-500',
  final:   'text-green-500',
}

const AUTOSAVE_MS = 1500

export default function Chapters() {
  const { projectId, chapterId } = useParams()
  const navigate = useNavigate()
  const { chapters, fetchChapters, createChapter, updateChapter, deleteChapter } =
    useChapterStore()

  const activeChapter = chapters.find((c) => c.id === chapterId) ?? null

  // Editor state
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [status, setStatus] = useState<string>('draft')
  const [saved, setSaved] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showAi, setShowAi] = useState(false)

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)
  useEffect(() => () => { mountedRef.current = false }, [])

  // Load chapters on project change
  useEffect(() => {
    if (projectId) fetchChapters(projectId)
  }, [projectId, fetchChapters])

  // Populate editor when active chapter changes
  useEffect(() => {
    if (activeChapter) {
      setTitle(activeChapter.title ?? '')
      setContent(activeChapter.content ?? '')
      setStatus(activeChapter.status ?? 'draft')
      setSaved(true)
    } else {
      setTitle('')
      setContent('')
      setStatus('draft')
      setSaved(true)
    }
    // Clear pending autosave when switching chapters
    if (timerRef.current) clearTimeout(timerRef.current)
  }, [activeChapter?.id])

  // ── Save ──────────────────────────────────────────────────────────────────

  const doSave = useCallback(
    async (t: string, c: string, s: string) => {
      if (!chapterId) return
      setSaving(true)
      try {
        await updateChapter(chapterId, { title: t, content: c, status: s })
        if (mountedRef.current) setSaved(true)
      } finally {
        if (mountedRef.current) setSaving(false)
      }
    },
    [chapterId, updateChapter],
  )

  const scheduleAutosave = useCallback(
    (t: string, c: string, s: string) => {
      setSaved(false)
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => doSave(t, c, s), AUTOSAVE_MS)
    },
    [doSave],
  )

  const onTitleChange = (v: string) => {
    setTitle(v)
    scheduleAutosave(v, content, status)
  }

  const onContentChange = (v: string) => {
    setContent(v)
    scheduleAutosave(title, v, status)
  }

  const onStatusChange = (v: string) => {
    setStatus(v)
    scheduleAutosave(title, content, v)
  }

  const onInsertText = useCallback((text: string) => {
    setContent((prev) => {
      const updated = prev ? prev + '\n\n' + text : text
      scheduleAutosave(title, updated, status)
      return updated
    })
  }, [title, status, scheduleAutosave])

  // Ctrl+S manual save
  const onKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      if (timerRef.current) clearTimeout(timerRef.current)
      doSave(title, content, status)
    }
  }

  // ── Create / delete ───────────────────────────────────────────────────────

  const newChapter = async () => {
    if (!projectId) return
    const next = await createChapter({
      project_id: projectId,
      title: `Chương ${chapters.length + 1}`,
      content: '',
      status: 'draft',
      scene_order: chapters.length,
    })
    navigate(`/projects/${projectId}/chapters/${next.id}`)
  }

  const removeChapter = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Xóa chương này?')) return
    await deleteChapter(id)
    if (id === chapterId) navigate(`/projects/${projectId}/chapters`)
  }

  const wordCount = content.split(/\s+/).filter(Boolean).length

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── Chapter list sidebar ── */}
      <aside className="flex w-60 flex-col border-r border-slate-800/70 bg-slate-900/60">
        <div className="flex items-center justify-between border-b border-slate-800/70 px-3 py-2">
          <span className="text-xs font-semibold text-slate-300">Chapters</span>
          <button
            onClick={newChapter}
            title="New chapter"
            className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-1">
          {chapters.map((ch) => (
            <ChapterItem
              key={ch.id}
              chapter={ch}
              active={ch.id === chapterId}
              onClick={() => navigate(`/projects/${projectId}/chapters/${ch.id}`)}
              onDelete={(e) => removeChapter(ch.id, e)}
            />
          ))}
          {!chapters.length && (
            <p className="px-3 py-4 text-center text-xs text-slate-600">
              Chưa có chương nào.
            </p>
          )}
        </div>
      </aside>

      {/* ── Editor main area ── */}
      {activeChapter ? (
        <div className="flex flex-1 flex-col overflow-hidden" onKeyDown={onKeyDown}>
          {/* Toolbar */}
          <div className="flex items-center gap-3 border-b border-slate-800/70 bg-slate-950 px-4 py-2">
            <input
              className="flex-1 bg-transparent text-base font-semibold text-slate-100 placeholder:text-slate-600 outline-none"
              value={title}
              onChange={(e) => onTitleChange(e.target.value)}
              placeholder="Tên chương"
            />

            <select
              className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-xs focus:outline-none"
              value={status}
              onChange={(e) => onStatusChange(e.target.value)}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            {/* Save indicator */}
            <div className="flex items-center gap-1 text-xs text-slate-500">
              {saving ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : saved ? (
                <CheckCircle className="h-3.5 w-3.5 text-green-600" />
              ) : (
                <Save className="h-3.5 w-3.5 text-yellow-500" />
              )}
              <span>{saving ? 'Lưu…' : saved ? 'Đã lưu' : 'Chưa lưu'}</span>
            </div>

            {/* AI toggle */}
            <button
              onClick={() => setShowAi((v) => !v)}
              title="AI Panel"
              className={`rounded p-1.5 transition-colors ${
                showAi
                  ? 'bg-indigo-900/50 text-indigo-300'
                  : 'text-slate-500 hover:bg-slate-800 hover:text-slate-300'
              }`}
            >
              <Bot className="h-4 w-4" />
            </button>
          </div>

          {/* Writing area */}
          <textarea
            className="flex-1 resize-none bg-transparent px-6 py-5 font-serif text-[15px] leading-relaxed text-slate-200 placeholder:text-slate-700 outline-none"
            value={content}
            onChange={(e) => onContentChange(e.target.value)}
            placeholder="Bắt đầu viết…  (Ctrl+S để lưu)"
            spellCheck={false}
          />

          {/* Status bar */}
          <div className="flex items-center justify-between border-t border-slate-800/70 bg-slate-950 px-4 py-1.5 text-xs text-slate-600">
            <span>{wordCount.toLocaleString()} từ</span>
            <span className={STATUS_COLOR[status] ?? 'text-slate-500'}>{status}</span>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-slate-600">
          <FileText className="h-12 w-12 opacity-20" />
          <p className="text-sm">Chọn chương từ danh sách hoặc tạo chương mới</p>
          <button
            onClick={newChapter}
            className="mt-1 flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            Tạo chương đầu tiên
          </button>
        </div>
      )}

      {/* ── AI Agent panel ── */}
      {showAi && (
        <div className="border-l border-slate-800">
          <AgentPanel
            projectId={projectId}
            chapterId={chapterId}
            chapterTitle={activeChapter?.title ?? null}
            onInsertText={onInsertText}
          />
        </div>
      )}
    </div>
  )
}

// ── Chapter list item ─────────────────────────────────────────────────────────

function ChapterItem({
  chapter,
  active,
  onClick,
  onDelete,
}: {
  chapter: Chapter
  active: boolean
  onClick: () => void
  onDelete: (e: React.MouseEvent) => void
}) {
  return (
    <button
      onClick={onClick}
      className={`group flex w-full items-center gap-2 px-3 py-2 text-left transition-colors ${
        active
          ? 'bg-slate-800 text-slate-100'
          : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
      }`}
    >
      <FileText className="h-3.5 w-3.5 shrink-0 text-slate-600" />
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm">{chapter.title || 'Untitled'}</div>
        <div className={`text-[10px] ${STATUS_COLOR[chapter.status ?? 'draft'] ?? 'text-slate-500'}`}>
          {chapter.status ?? 'draft'}
          {chapter.word_count ? ` · ${chapter.word_count.toLocaleString()} từ` : ''}
        </div>
      </div>
      <button
        onClick={onDelete}
        className="hidden shrink-0 rounded p-0.5 text-slate-600 hover:text-red-400 group-hover:block"
        title="Xóa chương"
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </button>
  )
}
