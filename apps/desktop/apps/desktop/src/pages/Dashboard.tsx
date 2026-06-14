import { useCallback, useEffect, useState } from 'react'
import { ArrowRight, Loader2, RefreshCw } from 'lucide-react'
import { api } from '../lib/api'

export type AppInfo = {
  app: string
  version: string
  python: string
  description: string
  repo: string
  error?: string
}

export type UpdateSummary = {
  readonly update_available: boolean
  readonly new_commits: number
  readonly latest_commit?: string
  readonly error?: string
}

export type UpdateApplyResult = {
  readonly success: boolean
  readonly message: string
  readonly commit?: string
}

export default function Dashboard() {
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

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-800 bg-slate-900 p-5 space-y-3">
        <h1 className="text-xl font-bold text-slate-100">Dashboard</h1>
        <p className="text-sm text-slate-400">Trạng thái app và cập nhật tự động.</p>
        {updateMessage && <p className="text-sm text-red-400">{updateMessage}</p>}
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm text-slate-300">Đang chạy: <b>{appInfo?.version || '?'}</b></span>
          {updateSummary && updateSummary.update_available && (
            <span className="rounded-full bg-green-900/50 px-3 py-1 text-sm text-green-300">
              Có bản mới ({updateSummary.new_commits} commit(s))
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button onClick={checkForUpdates} disabled={isCheckingUpdate} className="inline-flex items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40">
            {isCheckingUpdate ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {isCheckingUpdate ? 'Đang kiểm tra...' : 'Kiểm tra lại'}
          </button>
          {updateSummary && updateSummary.update_available && (
            <button onClick={applyUpdate} disabled={isApplyingUpdate} className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700 disabled:opacity-40">
              {isApplyingUpdate ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
              {isApplyingUpdate ? 'Đang cập nhật...' : 'Cập nhật ngay'}
            </button>
          )}
        </div>
      </section>
    </div>
  )
}
