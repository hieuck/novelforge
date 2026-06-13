import { useCallback, useEffect, useState } from 'react'
import { ArrowRight, Loader2, RefreshCw } from 'lucide-react'
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

type UpdateApplyResult = {
  readonly success: boolean
  readonly message: string
  readonly commit?: string
}

export default function Dashboard() {
  const { projects, fetchProjects, createProject } = useProjectStore()
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null)
  const [updateSummary, setUpdateSummary] = useState<UpdateSummary | null>(null)
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false)
  const [isApplyingUpdate, setIsApplyingUpdate] = useState(false)
  const [updateMessage, setUpdateMessage] = useState<string | null>(null)

  const checkForUpdates = useCallback(async () => {
    setIsCheckingUpdate(true)
    setUpdateMessage(null)
    try {
      const response = await api.get<UpdateSummary>('/update/check')
      setUpdateSummary(response)
    } catch (err) {
      setUpdateMessage(err instanceof Error ? err.message : 'Không kiểm tra được cập nhật.')
    } finally {
      setIsCheckingUpdate(false)
    }
  }, [])

  const applyUpdate = useCallback(async () => {
    setIsApplyingUpdate(true)
    setUpdateMessage(null)
    try {
      const response = await api.post<UpdateApplyResult>('/update/apply', {})
      if (!response.success) throw new Error(response.message)
      setUpdateMessage('Đã cập nhật. Vui lòng khởi động lại NovelForge để áp dụng phiên bản mới.')
      setUpdateSummary({ update_available: false, new_commits: 0, latest_commit: response.commit })
    } catch (err) {
      setUpdateMessage(err instanceof Error ? err.message : 'Cập nhật thất bại.')
    } finally {
      setIsApplyingUpdate(false)
    }
  }, [])

  useEffect(() => {
    api.get<AppInfo>('/settings/about').then(setAppInfo).catch(() => setAppInfo({
      app: 'NovelForge',
      version: '?',
      python: '?',
      description: 'Offline-first AI writing studio',
      repo: 'https://github.com/hieuck/novelforge',
      error: 'Failed to load',
    }))
    checkForUpdates()
    const interval = setInterval(checkForUpdates, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [checkForUpdates])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const newProject = async () => {
    await createProject({ title: 'Untitled project', status: 'active' } as any)
    await fetchProjects()
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-slate-400">Quản lý project truyện của bạn</p>
        </div>
        <button onClick={newProject} className="rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-100">
          Tạo project mới
        </button>
      </div>
      <div className="grid gap-3">
        {projects.map((p: any) => (
          <a key={p.id} href={`/projects/${p.id}`} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 block">
            <div className="font-medium">{p.title}</div>
            {p.genre && <div className="text-xs text-slate-400">{p.genre}</div>}
            {p.updated_at && (
              <div className="mt-1 text-xs text-slate-500">Cập nhật: {new Date(p.updated_at).toLocaleString()}</div>
            )}
          </a>
        ))}
        {!projects.length && <div className="text-sm text-slate-500">Chưa có project nào.</div>}
      </div>
    </div>
  )
}
