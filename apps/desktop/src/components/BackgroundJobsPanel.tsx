/**
 * BackgroundJobsPanel — submit & monitor autonomous agent jobs.
 *
 * Agent jobs run in the background on the engine without a live WS panel.
 * This panel lets users submit tasks, see all queued/running/done jobs for
 * the current project, and stream live progress logs for any active job.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Play, Square, Trash2, Loader2, CheckCircle, AlertCircle,
  Clock, Sparkles, ChevronDown, ChevronUp, RefreshCw,
} from 'lucide-react'
import { api, wsUrl } from '../lib/api'
import i18n from '../i18n'

// ── Types ─────────────────────────────────────────────────────────────────────

interface AgentJob {
  id: string
  project_id: string
  kind: string
  status: 'queued' | 'running' | 'done' | 'failed' | 'cancelled'
  params: { task?: string; language?: string } | null
  result: {
    logs?: string[]
    meta?: { plan?: Array<{ step: number; tool: string; description: string }> }
    output?: { summary?: string; steps_completed?: number }
  } | null
  error: string | null
  created_at: string | null
  updated_at: string | null
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_CONFIG = {
  queued:    { color: 'text-slate-400',  bg: 'bg-slate-900',      icon: <Clock className="h-3.5 w-3.5" /> },
  running:   { color: 'text-yellow-400', bg: 'bg-yellow-950/30',  icon: <Loader2 className="h-3.5 w-3.5 animate-spin" /> },
  done:      { color: 'text-green-400',  bg: 'bg-green-950/30',   icon: <CheckCircle className="h-3.5 w-3.5" /> },
  failed:    { color: 'text-red-400',    bg: 'bg-red-950/30',     icon: <AlertCircle className="h-3.5 w-3.5" /> },
  cancelled: { color: 'text-slate-500',  bg: 'bg-slate-900',      icon: <Square className="h-3.5 w-3.5" /> },
} as const

function timeAgo(iso: string | null): string {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60_000) return i18n.t('jobs.just_now')
  if (diff < 3_600_000) return i18n.t('jobs.min_ago', { count: Math.floor(diff / 60_000) })
  return i18n.t('jobs.hour_ago', { count: Math.floor(diff / 3_600_000) })
}

// ── Job card ──────────────────────────────────────────────────────────────────

function JobCard({
  job,
  onCancel,
  onStream,
  streaming,
}: {
  job: AgentJob
  onCancel: (id: string) => void
  onStream: (id: string) => void
  streaming: string | null
}) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const cfg = STATUS_CONFIG[job.status]
  const task = job.params?.task ?? t('jobs.no_task')
  const logs = job.result?.logs ?? []
  const summary = job.result?.output?.summary
  const isActive = job.status === 'queued' || job.status === 'running'
  const isStreaming = streaming === job.id

  return (
    <div className={`rounded-lg border border-slate-800 p-3 space-y-2 ${cfg.bg}`}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className={cfg.color}>{cfg.icon}</span>
          <span className={`text-[10px] font-semibold uppercase tracking-wide ${cfg.color}`}>
            {t(`jobs.${job.status}`)}
          </span>
          {job.created_at && (
            <span className="text-[10px] text-slate-600">{timeAgo(job.created_at)}</span>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {(job.status === 'running') && (
            <button
              type="button"
              onClick={() => onStream(job.id)}
              title={isStreaming ? t('jobs.viewing_logs') : t('jobs.view_logs')}
              className={`rounded p-1 text-[10px] transition-colors ${
                isStreaming ? 'text-indigo-400' : 'text-slate-600 hover:text-slate-400'
              }`}
            >
              <Sparkles className="h-3 w-3" />
            </button>
          )}
          {isActive && (
            <button
              type="button"
              onClick={() => onCancel(job.id)}
              title={t('jobs.cancel_tooltip')}
              className="rounded p-1 text-slate-600 hover:text-red-400"
            >
              <Square className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Task text */}
      <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">{task}</p>

      {/* Summary (done jobs) */}
      {summary && (
        <p className="text-xs text-green-300 leading-relaxed">{summary}</p>
      )}

      {/* Error */}
      {job.error && (
        <p className="text-xs text-red-400">{job.error}</p>
      )}

      {/* Logs toggle */}
      {logs.length > 0 && (
        <div>
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-[10px] text-slate-600 hover:text-slate-400"
          >
            {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {t('jobs.log_entries', { count: logs.length })}
          </button>
          {expanded && (
            <div className="mt-1.5 max-h-32 overflow-y-auto rounded border border-slate-800 bg-slate-950 p-2 space-y-0.5">
              {logs.map((line, i) => (
                <p key={i} className="font-mono text-[10px] text-slate-500 leading-relaxed">{line}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────

interface BackgroundJobsPanelProps {
  projectId?: string | null
}

export default function BackgroundJobsPanel({ projectId: propId }: BackgroundJobsPanelProps) {
  const { t } = useTranslation()
  const params = useParams()
  const projectId = propId ?? params.projectId ?? null

  const [task, setTask] = useState('')
  const [language, setLanguage] = useState<'vi' | 'en'>('vi')
  const [submitting, setSubmitting] = useState(false)
  const [jobs, setJobs] = useState<AgentJob[]>([])
  const [loadingJobs, setLoadingJobs] = useState(false)
  const [streamingJobId, setStreamingJobId] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  // ── Load jobs ────────────────────────────────────────────────────────────
  const loadJobs = useCallback(async () => {
    if (!projectId) return
    setLoadingJobs(true)
    try {
      const data = await api.get<AgentJob[]>(`/projects/${projectId}/jobs?limit=20`)
      setJobs(data.filter((j) => j.kind === 'agent'))
    } catch {
      // silently ignore
    } finally {
      setLoadingJobs(false)
    }
  }, [projectId])

  useEffect(() => {
    loadJobs()
    // Poll every 5s to pick up background updates
    pollTimer.current = setInterval(loadJobs, 5000)
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current)
      wsRef.current?.close()
    }
  }, [loadJobs])

  // ── Submit job ───────────────────────────────────────────────────────────
  const submit = async () => {
    if (!task.trim() || !projectId || submitting) return
    setSubmitting(true)
    try {
      const job = await api.post<AgentJob>('/agent/jobs', {
        project_id: projectId,
        task: task.trim(),
        language,
      })
      setTask('')
      setJobs((prev) => [job, ...prev])
      // Immediately start streaming logs for the new job
      streamJob(job.id)
    } catch (e) {
      // show error inline — not critical
    } finally {
      setSubmitting(false)
    }
  }

  // ── Stream job logs ──────────────────────────────────────────────────────
  const streamJob = useCallback((jobId: string) => {
    wsRef.current?.close()
    setStreamingJobId(jobId)

    const ws = new WebSocket(wsUrl(`/ws/jobs/${jobId}`))
    wsRef.current = ws

    ws.onmessage = (e: MessageEvent) => {
      try {
        const updated = JSON.parse(e.data as string) as AgentJob
        if (updated.error && !updated.id) return // error frame
        setJobs((prev) =>
          prev.map((j) => (j.id === updated.id ? updated : j))
        )
        if (['done', 'failed', 'cancelled'].includes(updated.status)) {
          setStreamingJobId(null)
          ws.close()
          loadJobs() // final refresh
        }
      } catch { /* ignore */ }
    }

    ws.onclose = () => {
      setStreamingJobId((prev) => (prev === jobId ? null : prev))
    }
  }, [loadJobs])

  // ── Cancel job ───────────────────────────────────────────────────────────
  const cancelJob = async (jobId: string) => {
    try {
      await api.post(`/jobs/${jobId}/cancel`, {})
      setJobs((prev) =>
        prev.map((j) => (j.id === jobId ? { ...j, status: 'cancelled' as const } : j))
      )
      if (streamingJobId === jobId) {
        wsRef.current?.close()
        setStreamingJobId(null)
      }
    } catch { /* ignore */ }
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      submit()
    }
  }

  const activeCount = jobs.filter((j) => j.status === 'queued' || j.status === 'running').length

  return (
    <div className="flex h-full flex-col bg-slate-950">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-semibold text-slate-200">{t('jobs.panel_title')}</span>
          {activeCount > 0 && (
            <span className="rounded-full bg-yellow-900/60 px-1.5 py-0.5 text-[10px] text-yellow-300">
              {t('jobs.active_count', { count: activeCount })}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={loadJobs}
          disabled={loadingJobs}
          title={t('jobs.refresh_tooltip')}
          className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300 disabled:opacity-40"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loadingJobs ? 'animate-spin' : ''}`} />
        </button>
      </header>

      {/* Job list */}
      <div className="flex-1 space-y-2 overflow-y-auto p-3">
        {!projectId && (
          <p className="text-center text-xs text-slate-600">{t('jobs.no_project')}</p>
        )}

        {jobs.length === 0 && projectId && !loadingJobs && (
          <div className="mt-4 text-center text-xs text-slate-600">
            {t('jobs.empty')}
          </div>
        )}

        {jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            onCancel={cancelJob}
            onStream={streamJob}
            streaming={streamingJobId}
          />
        ))}
      </div>

      {/* Submit form */}
      <div className="border-t border-slate-800 p-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-600">{t('jobs.submit_title')}</span>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as 'vi' | 'en')}
            className="rounded border border-slate-800 bg-slate-900 px-1.5 py-0.5 text-[10px] text-slate-400 focus:outline-none"
          >
            <option value="vi">{t('jobs.lang_vi')}</option>
            <option value="en">{t('jobs.lang_en')}</option>
          </select>
        </div>
        <textarea
          className="h-20 w-full resize-none rounded-md border border-slate-800 bg-slate-900 p-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-700 focus:outline-none disabled:opacity-50"
          placeholder={t('jobs.task_placeholder')}
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={submitting || !projectId}
        />
        <button
          type="button"
          onClick={submit}
          disabled={!task.trim() || !projectId || submitting}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
        >
          {submitting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
          {submitting ? t('jobs.submitting') : t('jobs.submit')}
        </button>
      </div>
    </div>
  )
}
