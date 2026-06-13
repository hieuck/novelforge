import { useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Download, Upload, FileText, Archive, Code, Check, AlertCircle } from 'lucide-react'
import { api } from '../lib/api'

type ExportFmt = 'md' | 'txt' | 'html' | 'zip'

interface ImportResult {
  imported: number
  chapters: { id: string; title: string }[]
}

export default function Export() {
  const { projectId } = useParams()
  const [exporting, setExporting] = useState<ExportFmt | null>(null)
  const [importing, setImporting] = useState(false)
  const [importMode, setImportMode] = useState<'single' | 'split_h2'>('split_h2')
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const formats: { fmt: ExportFmt; label: string; desc: string; icon: React.ReactNode }[] = [
    { fmt: 'md',   label: 'Markdown',    desc: 'File .md — toàn bộ chương',               icon: <FileText className="h-5 w-5" /> },
    { fmt: 'txt',  label: 'Plain Text',  desc: 'Văn bản thuần, không định dạng',           icon: <FileText className="h-5 w-5" /> },
    { fmt: 'html', label: 'HTML',        desc: 'Web page đọc được, có style serif',        icon: <Code className="h-5 w-5" /> },
    { fmt: 'zip',  label: 'Project ZIP', desc: 'Backup đầy đủ: story + characters + lore', icon: <Archive className="h-5 w-5" /> },
  ]

  const doExport = async (fmt: ExportFmt) => {
    if (!projectId) return
    setExporting(fmt)
    setResult(null)
    try {
      const res = await fetch('/api/export', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, fmt }),
      })
      if (!res.ok) throw new Error(await res.text())
      const blob = await res.blob()
      const cd = res.headers.get('Content-Disposition') ?? ''
      const name = cd.match(/filename="([^"]+)"/)?.[1] ?? `export.${fmt}`
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = name
      a.click()
      URL.revokeObjectURL(url)
      setResult({ ok: true, msg: `Đã xuất ${name}` })
    } catch (e: any) {
      setResult({ ok: false, msg: e.message })
    } finally {
      setExporting(null)
    }
  }

  const doImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !projectId) return
    setImporting(true)
    setResult(null)
    try {
      const text = await file.text()
      const data = await api.post<ImportResult>('/import', {
        project_id: projectId,
        content: text,
        filename: file.name,
        mode: importMode,
      })
      setResult({
        ok: true,
        msg: `Import ${data.imported} chương: ${data.chapters.map((c) => c.title).join(', ')}`,
      })
    } catch (e: any) {
      setResult({ ok: false, msg: e.message })
    } finally {
      setImporting(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-1 text-xl font-bold text-slate-100">Export / Import</h1>
      <p className="mb-6 text-sm text-slate-500">Xuất truyện ra file hoặc import từ Markdown / TXT</p>

      <section className="mb-8">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Xuất truyện</h2>
        <div className="grid grid-cols-2 gap-3">
          {formats.map(({ fmt, label, desc, icon }) => (
            <button key={fmt} onClick={() => doExport(fmt)}
              disabled={!!exporting || !projectId}
              className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900 p-4 text-left transition-colors hover:border-slate-700 hover:bg-slate-800/60 disabled:opacity-40">
              <div className="mt-0.5 flex-shrink-0 text-indigo-400">{icon}</div>
              <div className="min-w-0 flex-1">
                <div className="font-medium text-slate-200">{exporting === fmt ? 'Đang xuất...' : label}</div>
                <div className="mt-0.5 text-xs text-slate-500">{desc}</div>
              </div>
              <Download className="ml-auto mt-1 h-4 w-4 flex-shrink-0 text-slate-600" />
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Import file</h2>
        <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900 p-4">
          <div className="flex gap-4">
            {(['split_h2', 'single'] as const).map((m) => (
              <label key={m} className="flex cursor-pointer items-center gap-2">
                <input type="radio" name="importMode" value={m}
                  checked={importMode === m} onChange={() => setImportMode(m)}
                  className="accent-indigo-500" />
                <span className="text-sm text-slate-300">
                  {m === 'split_h2' ? 'Tách theo ## heading' : 'Một chương'}
                </span>
              </label>
            ))}
          </div>
          <input ref={fileRef} type="file" accept=".md,.txt,.markdown"
            onChange={doImport} disabled={importing || !projectId}
            className="hidden" id="import-file" />
          <label htmlFor="import-file"
            className={`flex cursor-pointer items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate-700 p-8 text-sm text-slate-400 transition-colors hover:border-indigo-700 hover:text-slate-200 ${importing || !projectId ? 'pointer-events-none opacity-40' : ''}`}>
            <Upload className="h-5 w-5" />
            {importing ? 'Đang import...' : 'Chọn file .md hoặc .txt'}
          </label>
          <p className="text-xs text-slate-600">Chế độ "## heading": tách file thành nhiều chương theo H2.</p>
        </div>
      </section>

      {result && (
        <div className={`mt-4 flex items-start gap-2 rounded-lg border p-3 text-sm ${result.ok ? 'border-green-900 bg-green-950 text-green-300' : 'border-red-900 bg-red-950 text-red-300'}`}>
          {result.ok ? <Check className="mt-0.5 h-4 w-4 flex-shrink-0" /> : <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />}
          <span>{result.msg}</span>
        </div>
      )}
      {!projectId && (
        <div className="mt-4 rounded-lg border border-amber-900 bg-amber-950 p-3 text-sm text-amber-300">
          Hãy chọn project từ sidebar trước khi export / import.
        </div>
      )}
    </div>
  )
}
