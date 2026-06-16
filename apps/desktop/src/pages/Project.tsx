import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Save, CheckCircle, Loader2, BookOpen, AlignLeft, Paintbrush, Sparkles } from 'lucide-react'
import { useProjectStore } from '../stores/projectStore'
import { wsUrl } from '../lib/api'
import type { Project } from '../types'

type Tab = 'overview' | 'style'

const AUTOSAVE_DELAY = 1500

export default function ProjectPage() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const { projects, fetchProjects, updateProject } = useProjectStore()

  const project = projects.find((p) => p.id === projectId)

  const [tab, setTab] = useState<Tab>('overview')
  const [form, setForm] = useState<Partial<Project>>({})
  const [saved, setSaved] = useState(true)
  const [saving, setSaving] = useState(false)
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [summaryStream, setSummaryStream] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const streamBuf = useRef('')
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Cleanup on unmount
  const mountedRef = useRef(true)
  useEffect(() => () => {
    mountedRef.current = false
    if (timer.current) clearTimeout(timer.current)
    wsRef.current?.close()
  }, [])

  const generateSummary = () => {
    if (!projectId || generatingSummary) return
    setGeneratingSummary(true)
    setSummaryStream('')
    streamBuf.current = ''

    const ws = new WebSocket(wsUrl('/ws/ai'))
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({
        project_id: projectId,
        action: 'summarize_project',
        text: '',
        instruction: 'Viết tóm tắt ngắn gọn, súc tích về toàn bộ project dựa trên thông tin hiện có.',
        history: [],
      }))
    }

    ws.onmessage = (e: MessageEvent) => {
      try {
        const msg = JSON.parse(e.data as string) as { delta?: string; done?: boolean; full?: string; error?: string }
        if (msg.error) { if (mountedRef.current) setGeneratingSummary(false); ws.close(); return }
        if (msg.delta) {
          streamBuf.current += msg.delta
          if (mountedRef.current) setSummaryStream(streamBuf.current)
        }
        if (msg.done) {
          const generated = msg.full ?? streamBuf.current
          if (mountedRef.current) {
            const updated = { ...form, summary: generated }
            setForm(updated)
            scheduleAutosave(updated)
            setSummaryStream('')
            setGeneratingSummary(false)
          }
          streamBuf.current = ''
          ws.close()
        }
      } catch { /* ignore */ }
    }

    ws.onerror = () => { if (mountedRef.current) setGeneratingSummary(false) }
    ws.onclose = () => { if (mountedRef.current) setGeneratingSummary(false) }
  }

  useEffect(() => {
    if (!projects.length) fetchProjects()
  }, [])

  useEffect(() => {
    if (project) {
      setForm({
        title: project.title ?? '',
        description: project.description ?? '',
        genre: project.genre ?? '',
        language: project.language ?? 'vi',
        style_guide: project.style_guide ?? '',
        summary: project.summary ?? '',
      })
      setSaved(true)
    }
  }, [project?.id])

  const scheduleAutosave = (updates: Partial<Project>) => {
    setSaved(false)
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(async () => {
      if (!projectId) return
      setSaving(true)
      await updateProject(projectId, updates)
      setSaved(true)
      setSaving(false)
    }, AUTOSAVE_DELAY)
  }

  const change = (key: keyof Project, value: string) => {
    const updated = { ...form, [key]: value }
    setForm(updated)
    scheduleAutosave(updated)
  }

  if (!project) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        {t('project.loading')}
      </div>
    )
  }

  const inputCls =
    'w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none'
  const labelCls = 'block text-xs font-medium text-slate-400 mb-1'

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <div className="flex items-center gap-3">
          <BookOpen className="h-5 w-5 text-indigo-400" />
          <h1 className="text-lg font-semibold text-slate-100 truncate max-w-xs">
            {project.title}
          </h1>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          {saving ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-500" />
          ) : saved ? (
            <CheckCircle className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <Save className="h-3.5 w-3.5 text-yellow-500" />
          )}
          {saving ? t('project.saving') : saved ? t('project.saved') : t('project.unsaved')}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-800 px-6 py-0">
        {(['overview', 'style'] as Tab[]).map((tabName) => (
          <button
            key={tabName}
            onClick={() => setTab(tabName)}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-xs font-medium transition-colors ${
              tab === tabName
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}
          >
            {tabName === 'overview' ? <AlignLeft className="h-3.5 w-3.5" /> : <Paintbrush className="h-3.5 w-3.5" />}
            {tabName === 'overview' ? t('project.tab_overview') : t('project.tab_style')}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {tab === 'overview' && (
          <div className="mx-auto max-w-2xl space-y-4">
            <div>
              <label className={labelCls}>{t('project.title_label')}</label>
              <input
                className={inputCls}
                value={form.title ?? ''}
                onChange={(e) => change('title', e.target.value)}
                placeholder={t('project.title_placeholder')}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>{t('project.genre_label')}</label>
                <input
                  className={inputCls}
                  value={form.genre ?? ''}
                  onChange={(e) => change('genre', e.target.value)}
                  placeholder={t('project.genre_placeholder')}
                />
              </div>
              <div>
                <label className={labelCls}>{t('project.language_label')}</label>
                <select
                  className={inputCls}
                  value={form.language ?? 'vi'}
                  onChange={(e) => change('language', e.target.value)}
                >
                  <option value="vi">{t('project.lang_vi')}</option>
                  <option value="en">{t('project.lang_en')}</option>
                </select>
              </div>
            </div>

            <div>
              <label className={labelCls}>{t('project.description_label')}</label>
              <textarea
                className={inputCls}
                rows={3}
                value={form.description ?? ''}
                onChange={(e) => change('description', e.target.value)}
                placeholder={t('project.description_placeholder')}
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className={labelCls}>
                  {t('project.summary_label')}{' '}
                  <span className="text-slate-600">{t('project.summary_hint')}</span>
                </label>
                <button
                  type="button"
                  onClick={generateSummary}
                  disabled={generatingSummary || !projectId}
                  className="flex items-center gap-1.5 rounded-md border border-indigo-800/60 bg-indigo-900/30 px-2.5 py-1 text-[11px] text-indigo-300 hover:bg-indigo-900/50 disabled:opacity-40 transition-colors"
                >
                  {generatingSummary
                    ? <Loader2 className="h-3 w-3 animate-spin" />
                    : <Sparkles className="h-3 w-3" />}
                  {generatingSummary ? t('project.summary_generating') : t('project.summary_generate')}
                </button>
              </div>
              {summaryStream ? (
                <div className="w-full rounded-md border border-indigo-900/50 bg-slate-900 px-3 py-2 text-sm text-slate-300 leading-relaxed min-h-[120px] whitespace-pre-wrap">
                  {summaryStream}
                  <span className="inline-block h-3.5 w-0.5 bg-indigo-400 animate-pulse ml-0.5" />
                </div>
              ) : (
                <textarea
                  className={inputCls}
                  rows={5}
                  value={form.summary ?? ''}
                  onChange={(e) => change('summary', e.target.value)}
                  placeholder={t('project.summary_placeholder')}
                />
              )}
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900 p-3 text-xs text-slate-500">
              <div className="font-medium text-slate-400 mb-1">{t('project.stats_label')}</div>
              <div className="grid grid-cols-3 gap-3">
                <Stat label={t('project.stat_created')} value={project.created_at ? new Date(project.created_at).toLocaleDateString() : '—'} />
                <Stat label={t('project.stat_updated')} value={project.updated_at ? new Date(project.updated_at).toLocaleDateString() : '—'} />
                <Stat label={t('project.stat_language')} value={project.language?.toUpperCase() ?? 'VI'} />
              </div>
            </div>
          </div>
        )}

        {tab === 'style' && (
          <div className="mx-auto max-w-2xl space-y-4">
            <div className="rounded-lg border border-indigo-900/40 bg-indigo-950/20 p-3 text-xs text-indigo-300">
              <strong>{t('project.style_guide_heading')}</strong>{' '}
              {t('project.style_guide_info')}
            </div>

            <div>
              <label className={labelCls}>{t('project.style_guide_label')}</label>
              <textarea
                className={`${inputCls} font-mono text-xs leading-relaxed`}
                rows={14}
                value={form.style_guide ?? ''}
                onChange={(e) => change('style_guide', e.target.value)}
                placeholder={t('project.style_guide_placeholder')}
              />
            </div>

            <div>
              <label className={labelCls}>
                {t('project.notes_label')}{' '}
                <span className="text-slate-600">{t('project.notes_hint')}</span>
              </label>
              <textarea
                className={`${inputCls} leading-relaxed`}
                rows={6}
                value={form.description ?? ''}
                onChange={(e) => change('description', e.target.value)}
                placeholder={t('project.notes_placeholder')}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-slate-600">{label}</div>
      <div className="text-slate-400">{value}</div>
    </div>
  )
}
