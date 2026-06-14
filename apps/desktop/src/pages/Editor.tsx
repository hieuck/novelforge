import { useEffect, useRef, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../lib/api'
import { useProjectStore } from '../stores/projectStore'
import { useChapterStore } from '../stores/chapterStore'
import { useParams, useLocation } from 'react-router-dom'

export default function Editor() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const projectId = id || ''
  const location = useLocation()
  const chapterId = new URLSearchParams(location.search).get('chapter') || ''
  const [text, setText] = useState('')
  const [status, setStatus] = useState(t('page_editor.loading'))
  const { projects, fetchProjects } = useProjectStore()
  const { chapters, fetchChapters } = useChapterStore()
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (projectId) fetchChapters(projectId)
  }, [projectId])

  useEffect(() => {
    if (chapterId) {
      const chapter = chapters.find((item) => item.id === chapterId)
      if (chapter && chapter.content !== undefined) {
        setText(chapter.content)
        setStatus(t('page_editor.editing', { title: chapter.title }))
        setTimeout(() => inputRef.current?.focus(), 50)
        return
      }
    }

    if (!projects.length) {
      setStatus(t('page_editor.no_project'))
      return
    }

    setText('')
    setStatus(t('page_editor.select_hint'))
    inputRef.current?.focus()
  }, [chapterId, chapters, projects])

  const saveChapter = async () => {
    if (!projectId) return
    setSaving(true)
    setStatus(t('page_editor.saving'))
    try {
      let chapter = chapters.find((item) => item.id === chapterId)
      if (!chapter) {
        const created = await api.post<any>('/api/chapters', { project_id: projectId, title: t('page_editor.new_chapter'), content: text })
        chapter = created
      } else {
        await api.patch(`/api/chapters/${chapter.id}`, { title: chapter.title, content: text })
      }
      await fetchChapters(projectId)
      setStatus(t('page_editor.saved', { title: chapter?.title ?? t('page_editor.new_chapter') }))
    } catch (error) {
      setStatus(t('page_editor.save_error', { error: error instanceof Error ? error.message : 'unknown' }))
    } finally {
      setSaving(false)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
      event.preventDefault()
      saveChapter()
    }
  }

  return (
    <div className="h-[calc(100vh-8rem)] rounded-lg border border-slate-800 bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2">
        <div className="text-sm text-slate-300">{status}</div>
        <button
          onClick={saveChapter}
          disabled={saving}
          className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40"
        >
          {t('page_editor.save')}
        </button>
      </div>
      <textarea
        ref={inputRef}
        value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={t('page_editor.start_placeholder')}
        className="h-[calc(100%-3.2rem)] w-full resize-none bg-transparent p-4 font-mono text-sm leading-relaxed text-slate-200 outline-none"
      />
    </div>
  )
}
