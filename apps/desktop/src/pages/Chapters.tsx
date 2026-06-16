import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Plus, Trash2, CheckCircle, Save, Loader2,
  FileText,
} from 'lucide-react'
import { api } from '../lib/api'
import { useChapterStore } from '../stores/chapterStore'

import type { Chapter } from '../types'

const STATUS_OPTIONS = ['draft', 'revised', 'final'] as const
const STATUS_COLOR: Record<string, string> = {
  draft:   'text-slate-500',
  revised: 'text-yellow-500',
  final:   'text-green-500',
}

const AUTOSAVE_MS = 1500

export default function Chapters() {
  const { t } = useTranslation()
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
  const [sceneUrl, setSceneUrl] = useState<string | null>(null)
  const [previewImg, setPreviewImg] = useState<string | null>(null)
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [zenMode, setZenMode] = useState(false)
  const [preview, setPreview] = useState(false)

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
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



  // Warn on unsaved changes before closing
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!saved) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [saved])

  // Global keyboard shortcuts
  // Focus editor when switching chapters
  useEffect(() => {
    if (textareaRef.current && chapterId) {
      textareaRef.current.focus()
    }
  }, [chapterId])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === '?' && !(e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        setShowShortcuts((v) => !v)
        return
      }
      const ctrl = e.ctrlKey || e.metaKey
      if (e.key === 'Escape' && !ctrl) {
        if (zenMode) { setZenMode(false); return }
        if (showShortcuts) { setShowShortcuts(false); return }
        if (previewImg) { setPreviewImg(null); return }
        navigate(projectId ? `/projects/${projectId}` : '/')
        return
      }
      if (ctrl && e.shiftKey && e.key === 'P') {
        e.preventDefault()
        setPreview((v) => !v)
        return
      }
      if ((ctrl && e.shiftKey && e.key === 'F') || e.key === 'F11') {
        e.preventDefault()
        setZenMode((v) => !v)
        return
      }
      if (ctrl && e.key === 'n') {
        e.preventDefault()
        if (!projectId) return
        const n = useChapterStore.getState().chapters.length + 1
        useChapterStore.getState().createChapter({ project_id: projectId, title: t('chapters.new_title', { n }), content: '', status: 'draft', scene_order: n }).then((ch) => navigate(`/projects/${projectId}/chapters/${ch.id}`))
      }
      if (ctrl && e.key === 'e' && textareaRef.current) {
        e.preventDefault()
        textareaRef.current.focus()
      }
      if (ctrl && e.shiftKey && e.key === 'D' && chapterId) {
        e.preventDefault()
        if (!confirm(t('chapters.delete_confirm'))) return
        useChapterStore.getState().deleteChapter(chapterId)
        navigate(`/projects/${projectId}/chapters`)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [chapterId, projectId, zenMode])

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
      title: t('chapters.new_title', { n: chapters.length + 1 }),
      content: '',
      status: 'draft',
      scene_order: chapters.length,
    })
    navigate(`/projects/${projectId}/chapters/${next.id}`)
  }

  const removeChapter = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(t('chapters.delete_confirm'))) return
    await deleteChapter(id)
    if (id === chapterId) navigate(`/projects/${projectId}/chapters`)
  }

  const wordCount = content.split(/\s+/).filter(Boolean).length
  const charCount = content.length

  return (
    <div className={`flex h-full overflow-hidden ${zenMode ? 'bg-black' : ''}`}>
      {/* ── Chapter list sidebar ── */}
      {!zenMode && (
      <aside className="flex w-60 flex-col border-r border-slate-800/70 bg-slate-900/60">
        <div className="flex items-center justify-between border-b border-slate-800/70 px-3 py-2">
          <span className="text-xs font-semibold text-slate-300">{t('chapters.sidebar_title')}</span>
          <button
            onClick={newChapter}
            title={t('chapters.new_chapter_tooltip')}
            className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-1"
          onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move' }}
          onDrop={async (e) => {
            e.preventDefault()
            const raw = e.dataTransfer.getData('text/plain')
            if (!raw) return
            const { chapterId: dragId } = JSON.parse(raw)
            if (!dragId || dragId === chapterId) return
            const ordered = [...chapters].sort((a, b) => (a.scene_order ?? 0) - (b.scene_order ?? 0))
            const fromIdx = ordered.findIndex((c) => c.id === dragId)
            if (fromIdx < 0) return
            const [moved] = ordered.splice(fromIdx, 1)
            ordered.splice(ordered.length, 0, moved)
            await api.post('/chapters/reorder', { ordered_ids: ordered.map((c) => c.id) })
            fetchChapters(projectId!)
          }}>
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
              {t('chapters.empty_list')}
            </p>
          )}
        </div>
      </aside>
      )}

      {/* ── Editor main area ── */}
      {activeChapter ? (
        <div className="flex flex-1 flex-col overflow-hidden" onKeyDown={onKeyDown}>
          {/* Toolbar */}
          <div className="flex items-center gap-3 border-b border-slate-800/70 bg-slate-950 px-4 py-2">
            <input
              className="flex-1 bg-transparent text-base font-semibold text-slate-100 placeholder:text-slate-600 outline-none"
              value={title}
              onChange={(e) => onTitleChange(e.target.value)}
              placeholder={t('chapters.title_placeholder')}
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
              <span>{saving ? t('chapters.saving') : saved ? t('chapters.saved') : t('chapters.unsaved')}</span>
            </div>

            {/* Preview toggle */}
            <button onClick={() => setPreview((v) => !v)}
              className={`rounded-md border px-2 py-1 text-[11px] transition-colors ${
                preview ? 'border-indigo-700 bg-indigo-900/30 text-indigo-300' : 'border-slate-700 text-slate-500 hover:border-slate-500'
              }`}
              title={preview ? 'Edit mode' : 'Preview mode'}
            >
              {preview ? '✎ Edit' : '👁 Preview'}
            </button>

            {/* Zen mode toggle */}
            <button onClick={() => setZenMode((v) => !v)}
              className={`rounded-md border px-2 py-1 text-[11px] transition-colors ${
                zenMode ? 'border-indigo-700 bg-indigo-900/30 text-indigo-300' : 'border-slate-700 text-slate-500 hover:border-slate-500'
              }`}
              title={zenMode ? 'Exit full-screen' : 'Full-screen writing'}
            >
              {zenMode ? '✕ Exit' : '⛶ Full'}
            </button>

            {/* Scene illustration */}
            {chapterId && activeChapter && (
              <button
                onClick={async () => {
                  const prompt = `Scene: ${activeChapter.title}, ${content?.slice(0, 200) || ''}, cinematic`.trim()
                  const data = await api.post<{ url: string }>('/generate/image', { prompt, size: 'medium', project_id: projectId, entity_type: 'chapter', entity_id: chapterId }, true)
                  if (data) {
                    await updateChapter(chapterId, { illustration_url: data.url })
                    setSceneUrl(data.url)
                  }
                }}
                className="flex items-center gap-1.5 rounded-md border border-slate-700 px-2.5 py-1 text-[11px] text-slate-400 hover:border-slate-500 hover:text-slate-200"
                title="Generate scene illustration"
              >
                🎨 Scene
              </button>
            )}
          </div>

          {/* Scene image display */}
          {(sceneUrl || activeChapter?.illustration_url) && (
            <div className="border-b border-slate-800">
              <img src={sceneUrl || activeChapter?.illustration_url || ''} alt="Scene"
                className="w-full max-h-64 object-cover cursor-pointer hover:opacity-90"
                onClick={() => setPreviewImg(sceneUrl || activeChapter?.illustration_url || '')} />
            </div>
          )}
          {previewImg && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={() => setPreviewImg(null)}>
              <img src={previewImg} className="max-h-[90vh] max-w-[90vw] object-contain" alt="preview" />
            </div>
          )}

          {showShortcuts && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowShortcuts(false)}>
              <div className="w-80 rounded-lg border border-slate-700 bg-slate-900 p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
                <h3 className="mb-3 text-sm font-semibold text-slate-100">Keyboard Shortcuts</h3>
                <div className="space-y-2 text-xs text-slate-400">
                  {[
                    ['Ctrl+N', 'New chapter'],
                    ['Ctrl+E', 'Focus editor'],
                    ['Ctrl+Shift+D', 'Delete chapter'],
                    ['Ctrl+Shift+P', 'Preview toggle'],
                    ['Ctrl+S', 'Save'],
                    ['F11 / Ctrl+Shift+F', 'Full-screen'],
                    ['Escape', 'Exit full-screen / Back'],
                    ['?', 'Toggle shortcuts'],
                    ['Click Scene 🎨', 'Generate illustration'],
                    ['Click portrait', 'Preview full size'],
                  ].map(([key, desc]) => (
                    <div key={key} className="flex justify-between">
                      <kbd className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">{key}</kbd>
                      <span>{desc}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Writing area */}
          {preview ? (
            <div className="flex-1 overflow-y-auto px-6 py-5 font-serif text-[15px] leading-relaxed text-slate-200 whitespace-pre-wrap">
              {content || <span className="text-slate-600 italic">No content</span>}
            </div>
          ) : (
            <textarea
              ref={textareaRef}
              className="flex-1 resize-none bg-transparent px-6 py-5 font-serif text-[15px] leading-relaxed text-slate-200 placeholder:text-slate-700 outline-none"
              value={content}
              onChange={(e) => onContentChange(e.target.value)}
              placeholder={t('chapters.content_placeholder')}
              spellCheck={false}
            />
          )}

          {/* Status bar */}
          <div className="flex items-center justify-between border-t border-slate-800/70 bg-slate-950 px-4 py-1.5 text-xs text-slate-600">
            <span className="flex gap-3">
              <span>{t('chapters.word_count', { count: wordCount })}</span>
              <span className="text-slate-600">{charCount.toLocaleString()} chars</span>
            </span>
            <span className={STATUS_COLOR[status] ?? 'text-slate-500'}>{status}</span>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-slate-600">
          <FileText className="h-12 w-12 opacity-20" />
          <p className="text-sm">{t('chapters.no_selection')}</p>
          <button
            onClick={newChapter}
            className="mt-1 flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            {t('chapters.create_first')}
          </button>
        </div>
      )}

      {/* AI Agent panel is now in App.tsx (right panel) */}
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
  const { t } = useTranslation()
  return (
    <div className="group flex items-center rounded-md px-1 transition-colors">
      <button
        draggable
        onDragStart={(e) => {
          const dragEvent = e as unknown as React.DragEvent
          dragEvent.dataTransfer.setData('text/plain', JSON.stringify({ chapterId: chapter.id }))
          dragEvent.dataTransfer.effectAllowed = 'move'
        }}
        onClick={onClick}
        className={`flex flex-1 items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors ${
          active
            ? 'bg-slate-800 text-slate-100'
            : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
        }`}
      >
        <FileText className="h-3.5 w-3.5 shrink-0 text-slate-600" />
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm">{chapter.title || t('chapters.untitled')}</div>
          <div className={`text-[10px] ${STATUS_COLOR[chapter.status ?? 'draft'] ?? 'text-slate-500'}`}>
            {chapter.status ?? 'draft'}
            {chapter.word_count ? ` · ${t('chapters.word_count', { count: chapter.word_count })}` : ''}
          </div>
        </div>
      </button>
      <button
        onClick={onDelete}
        className="shrink-0 rounded p-0.5 text-slate-600 hover:text-red-400"
        title={t('chapters.delete_tooltip')}
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  )
}
