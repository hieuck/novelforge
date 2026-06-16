import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Loader2, Film, Plus, Image as ImageIcon, Video } from 'lucide-react'
import { api } from '../lib/api'

interface Chapter {
  id: string; title?: string; content?: string; scene_order?: number; illustration_url?: string | null
}

export default function Storyboard() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [exportProgress, setExportProgress] = useState<{ current: number; total: number } | null>(null)
  const [dragIdx, setDragIdx] = useState<number | null>(null)

  const load = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const chData = await api.get<Chapter[]>(`/projects/${projectId}/chapters`)
      setChapters(chData)
    } catch { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => { load() }, [projectId])

  const getImageUrl = (ch: Chapter) => ch.illustration_url

  const handleGenerate = async (ch: Chapter) => {
    const prompt = `Scene: ${ch.title || 'Chapter'}, ${(ch.content || '').slice(0, 200)}, cinematic`.trim()
    const data = await api.post<{ url: string }>('/generate/image', { prompt, size: 'medium', project_id: projectId, entity_type: 'chapter', entity_id: ch.id }, true)
    if (data) {
      await api.patch(`/chapters/${ch.id}`, { illustration_url: data.url }, true)
      load()
    }
  }

  if (loading) {
    return <div className="flex h-full items-center justify-center text-slate-500"><Loader2 className="h-5 w-5 animate-spin mr-2" />Loading...</div>
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mx-auto max-w-6xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Film className="h-5 w-5 text-indigo-400" />
            <h1 className="text-xl font-bold text-slate-100">Storyboard</h1>
          </div>
          <div className="flex gap-2">
            <button onClick={async () => {
              if (!projectId) return
              setExporting(true)
              try {
                const { job_id } = await api.post<{ job_id: string }>(`/projects/${projectId}/storyboard/export-video`, {}, true)
                // Poll for completion
                const poll = async (): Promise<void> => {
                  const job = await api.get<{ status: string; result?: { message?: string; progress?: number; total?: number }; error?: string }>(`/jobs/${job_id}`)
                  if (job.result?.progress !== undefined) {
                    setExportProgress({ current: job.result.progress, total: job.result.total ?? 1 })
                  }
                  if (job.status === 'done') {
                    const r = await fetch(`/api/jobs/${job_id}/video`)
                    const blob = await r.blob()
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url; a.download = 'storyboard.mp4'; a.click()
                    URL.revokeObjectURL(url)
                    setExporting(false)
                    setExportProgress(null)
                  } else if (job.status === 'failed') {
                    alert(job.error || 'Export failed')
                    setExporting(false)
                    setExportProgress(null)
                  } else {
                    setTimeout(poll, 1000)
                  }
                }
                poll()
              } catch (e: any) { alert(e.message); setExporting(false) }
            }} disabled={exporting}
              className="flex items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40">
              {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Video className="h-4 w-4" />}
              {exporting
                ? exportProgress ? `Exporting ${exportProgress.current}/${exportProgress.total}...` : 'Exporting...'
                : 'Export Video'}
            </button>
            <button onClick={() => navigate(`/projects/${projectId}/chapters`)}
              className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700">
              <Plus className="h-4 w-4" /> Thêm chương
            </button>
          </div>
          {exporting && exportProgress && (
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                style={{ width: `${(exportProgress.current / exportProgress.total) * 100}%` }} />
            </div>
          )}
        </div>

        {chapters.length === 0 ? (
          <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-slate-800 p-16 text-center">
            <Film className="h-12 w-12 text-slate-700" />
            <div>
              <p className="text-sm font-medium text-slate-400">Storyboard trống</p>
              <p className="mt-1 text-xs text-slate-600">Tạo chapter trước, sau đó tạo scene illustrations để xây dựng storyboard.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {[...chapters].sort((a, b) => (a.scene_order ?? 0) - (b.scene_order ?? 0)).map((ch, idx) => {
              const imgUrl = getImageUrl(ch)
              const moveChapter = async (fromIdx: number, toIdx: number) => {
                const ordered = [...chapters].sort((a, b) => (a.scene_order ?? 0) - (b.scene_order ?? 0))
                const [moved] = ordered.splice(fromIdx, 1)
                ordered.splice(toIdx, 0, moved)
                const ok = await api.post('/chapters/reorder', { ordered_ids: ordered.map((c) => c.id) }, true)
                if (ok) load()
              }
              const isDragOver = dragIdx !== null && dragIdx !== idx
              return (
                <div key={ch.id}
                  draggable
                  onDragStart={() => setDragIdx(idx)}
                  onDragOver={(e) => { if (isDragOver) { e.preventDefault() } }}
                  onDrop={async (e) => {
                    e.preventDefault()
                    if (dragIdx === null || dragIdx === idx) { setDragIdx(null); return }
                    const ordered = [...chapters].sort((a, b) => (a.scene_order ?? 0) - (b.scene_order ?? 0))
                    const [moved] = ordered.splice(dragIdx, 1)
                    ordered.splice(idx, 0, moved)
                    const ok = await api.post('/chapters/reorder', { ordered_ids: ordered.map((c) => c.id) }, true)
                    if (ok) load()
                    setDragIdx(null)
                  }}
                  onDragEnd={() => setDragIdx(null)}
                  className={`flex gap-4 rounded-lg border p-4 transition-colors ${
                    dragIdx === idx
                      ? 'border-indigo-500 bg-indigo-950/30 opacity-50'
                      : isDragOver
                        ? 'border-indigo-500/50 bg-slate-900'
                        : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                  }`}>
                  <div className="flex flex-col items-center gap-1">
                    <button onClick={() => moveChapter(idx, idx - 1)} disabled={idx === 0}
                      className="h-6 w-6 rounded border border-slate-700 text-xs text-slate-500 hover:text-slate-200 disabled:opacity-20 disabled:cursor-not-allowed">▲</button>
                    <span className="text-sm font-bold text-indigo-400">{idx + 1}</span>
                    <button onClick={() => moveChapter(idx, idx + 1)} disabled={idx >= chapters.length - 1}
                      className="h-6 w-6 rounded border border-slate-700 text-xs text-slate-500 hover:text-slate-200 disabled:opacity-20 disabled:cursor-not-allowed">▼</button>
                  </div>
                  <div className="w-48 shrink-0">
                    {imgUrl ? (
                      <img src={imgUrl} alt={ch.title || ''} className="h-28 w-48 rounded-lg object-cover border border-slate-700" />
                    ) : (
                      <div className="flex h-28 w-48 items-center justify-center rounded-lg border border-dashed border-slate-700 bg-slate-800/50">
                        <button onClick={() => handleGenerate(ch)} className="flex flex-col items-center gap-1 text-slate-500 hover:text-slate-300">
                          <ImageIcon className="h-6 w-6" />
                          <span className="text-[10px]">Tạo ảnh</span>
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-slate-200 truncate">{ch.title || 'Untitled'}</h3>
                    <p className="mt-1 text-xs text-slate-500 line-clamp-3">{ch.content?.slice(0, 200) || ''}</p>
                    <div className="mt-2 flex gap-2">
                      <button onClick={() => navigate(`/projects/${projectId}/chapters/${ch.id}`)}
                        className="text-[10px] text-indigo-400 hover:text-indigo-300">Sửa</button>
                      {imgUrl && (
                        <button onClick={() => handleGenerate(ch)}
                          className="text-[10px] text-slate-500 hover:text-slate-300">Tạo lại ảnh</button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
