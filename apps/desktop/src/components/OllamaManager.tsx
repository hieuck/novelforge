import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Loader2, RefreshCw, Trash2, Download } from 'lucide-react'
import { api } from '../lib/api'

interface ModelInfo {
  name: string
  size?: number
  parameter_size?: string
  quantization?: string
}

function formatBytes(bytes: number): string {
  if (!bytes) return ''
  const gb = bytes / 1_000_000_000
  return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / 1_000_000).toFixed(0)} MB`
}

export default function OllamaManager() {
  const { t } = useTranslation()
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [pullName, setPullName] = useState('')
  const [pulling, setPulling] = useState(false)
  const [msg, setMsg] = useState<{ type: 'ok' | 'error'; text: string } | null>(null)

  const load = async () => {
    setLoading(true); setMsg(null)
    try {
      const data = await api.get<{ models: ModelInfo[]; error?: string }>('/settings/models?provider=ollama&base_url=http://localhost:11434')
      if (data.error) { setMsg({ type: 'error', text: data.error }); setModels([]) }
      else { setModels(data.models || []) }
    } catch (e: any) { setMsg({ type: 'error', text: e.message }) }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handlePull = async () => {
    const name = pullName.trim()
    if (!name) return
    setPulling(true); setMsg(null)
    try {
      const r = await api.post<{ success: boolean; message?: string; error?: string }>('/settings/models/pull', { name })
      if (r.success) { setMsg({ type: 'ok', text: r.message || 'OK' }); setPullName(''); load() }
      else { setMsg({ type: 'error', text: r.error || 'Failed' }) }
    } catch (e: any) { setMsg({ type: 'error', text: e.message }) }
    setPulling(false)
  }

  const handleDelete = async (name: string) => {
    if (!confirm(`Xóa model "${name}"?`)) return
    try {
      const res = await fetch(`/api/settings/models/${encodeURIComponent(name)}`, { method: 'DELETE' })
      const data = await res.json()
      if (data.success) { setMsg({ type: 'ok', text: `Đã xóa ${name}` }); load() }
      else { setMsg({ type: 'error', text: data.error || 'Failed' }) }
    } catch (e: any) { setMsg({ type: 'error', text: e.message }) }
  }

  const inp = 'w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-700 focus:outline-none'

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-300">Quản lý Model</span>
        <button onClick={load} disabled={loading} className="rounded p-1 text-slate-500 hover:text-slate-300" title={t('settings.load_models_tooltip')}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {msg && (
        <div className={`rounded-md px-3 py-2 text-xs ${msg.type === 'ok' ? 'bg-green-950/40 text-green-300 border border-green-800/60' : 'bg-red-950/40 text-red-300 border border-red-800/60'}`}>
          {msg.text}
        </div>
      )}

      {/* Model list */}
      {loading ? (
        <div className="flex items-center gap-2 text-xs text-slate-500 py-4">
          <Loader2 className="h-4 w-4 animate-spin" />
          Đang tải danh sách model...
        </div>
      ) : models.length === 0 ? (
        <div className="text-xs text-slate-600 py-4 text-center">Chưa có model nào. Pull model bên dưới.</div>
      ) : (
        <div className="space-y-1 max-h-60 overflow-y-auto">
          {models.map((m) => (
            <div key={m.name} className="group flex items-center gap-2 rounded-md border border-slate-800 bg-slate-900/60 px-3 py-2 hover:border-slate-700">
              <div className="flex-1 min-w-0">
                <div className="text-sm text-slate-200 truncate">{m.name}</div>
                <div className="flex gap-3 text-[10px] text-slate-500">
                  {m.parameter_size && <span>{m.parameter_size}</span>}
                  {m.size ? <span>{formatBytes(m.size)}</span> : null}
                  {m.quantization && <span>{m.quantization}</span>}
                </div>
              </div>
              <button onClick={() => handleDelete(m.name)} className="hidden group-hover:block rounded p-1 text-slate-600 hover:text-red-400" title="Xóa model">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Pull new model */}
      <div className="flex gap-2">
        <input className={inp} placeholder="Nhập tên model (vd: llama3.2:1b)" value={pullName} onChange={(e) => setPullName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handlePull()} />
        <button onClick={handlePull} disabled={pulling || !pullName.trim()}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50 whitespace-nowrap">
          {pulling ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          Pull
        </button>
      </div>
    </div>
  )
}
