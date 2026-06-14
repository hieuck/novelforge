import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Loader2, RefreshCw, BookOpen, Plus } from 'lucide-react'
import { api } from '../lib/api'
import { useProjectStore } from '../stores/projectStore'

type AppInfo = {
  app: string
  version: string
  python: string
  description: string
  repo: string
  error?: string
}

type UpdateSummary = {
  readonly update_available: boolean
  readonly new_commits: number
  readonly latest_commit?: string
  readonly error?: string
}

export default function Dashboard() {
  const { t } = useTranslation()
  const { projects, fetchProjects, createProject } = useProjectStore()
  const navigate = useNavigate()
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null)
  const [updateSummary, setUpdateSummary] = useState<UpdateSummary | null>(null)
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false)
  const [updateMessage, setUpdateMessage] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  const checkForUpdates = useCallback(async () => {
    setIsCheckingUpdate(true)
    setUpdateMessage(null)
    try {
      const response = await api.get<UpdateSummary>('/update/check')
      setUpdateSummary(response)
    } catch {
      // non-critical — silently ignore on dashboard
    } finally {
      setIsCheckingUpdate(false)
    }
  }, [])

  useEffect(() => {
    api.get<AppInfo>('/settings/about')
      .then(setAppInfo)
      .catch(() => setAppInfo({
        app: t('app.name'),
        version: '?',
        python: '?',
        description: t('app.tagline_long'),
        repo: t('app.repo'),
        error: t('app.engine_not_reachable'),
      }))
    checkForUpdates()
    const interval = setInterval(checkForUpdates, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [checkForUpdates])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const newProject = async () => {
    const title = prompt(t('dashboard.project_name_prompt'), t('dashboard.project_name_default'))?.trim()
    if (!title) return
    setCreating(true)
    try {
      const p = await createProject({ title })
      navigate(`/projects/${p.id}/chapters`)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-indigo-400" />
            <h1 className="text-2xl font-bold text-slate-100">{t('dashboard.title')}</h1>
          </div>
          <p className="mt-0.5 text-sm text-slate-500">
            {appInfo?.description ?? t('app.tagline_long')}
            {appInfo && !appInfo.error && (
              <span className="ml-2 text-slate-600">v{appInfo.version}</span>
            )}
          </p>
        </div>
        <button
          onClick={newProject}
          disabled={creating}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          {t('dashboard.create_project')}
        </button>
      </div>

      {/* Update banner */}
      {updateSummary?.update_available && (
        <div className="mb-4 flex items-center gap-3 rounded-lg border border-yellow-800/60 bg-yellow-950/30 px-4 py-3 text-sm text-yellow-300">
          <RefreshCw className="h-4 w-4 shrink-0" />
          <span>{t('dashboard.update_available', { count: updateSummary.new_commits })}</span>
        </div>
      )}

      {/* Project list */}
      <div className="space-y-2">
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-600">
          {t('dashboard.projects_count', { count: projects.length })}
        </h2>
        {projects.map((p) => (
          <button
            key={p.id}
            onClick={() => navigate(`/projects/${p.id}/chapters`)}
            className="block w-full rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-left transition-colors hover:border-slate-700 hover:bg-slate-900"
          >
            <div className="font-medium text-slate-100">{p.title}</div>
            <div className="mt-0.5 flex items-center gap-3 text-xs text-slate-500">
              {p.genre && <span>{p.genre}</span>}
              {p.updated_at && (
                <span>{t('dashboard.updated_at', { date: new Date(p.updated_at).toLocaleString() })}</span>
              )}
            </div>
          </button>
        ))}
        {!projects.length && (
          <div className="rounded-lg border border-dashed border-slate-800 p-8 text-center text-sm text-slate-600">
            {t('dashboard.empty_state')}
          </div>
        )}
      </div>
    </div>
  )
}
