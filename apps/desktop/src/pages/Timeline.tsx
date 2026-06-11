import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

export default function Timeline() {
  const { projectId } = useParams()
  const [items, setItems] = useState<any[]>([])
  const [form, setForm] = useState({ title: '', event_date: '', description: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetch(`/api/projects/${projectId}/timeline`)
      .then((r) => r.json())
      .then(setItems)
      .finally(() => setLoading(false))
  }, [projectId])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectId) return
    const res = await fetch('/api/timeline', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ...form, project_id: projectId }),
    })
    if (res.ok) {
      setForm({ title: '', event_date: '', description: '' })
      const r = await fetch(`/api/projects/${projectId}/timeline`)
      setItems(await r.json())
    }
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-2xl font-bold">Timeline</h1>
      <form onSubmit={submit} className="mb-6 grid gap-3 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <input
          className="rounded-md bg-slate-800 p-2"
          placeholder="Tiêu đề"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
        />
        <input
          className="rounded-md bg-slate-800 p-2"
          placeholder="Ngày/thứ tự"
          value={form.event_date}
          onChange={(e) => setForm({ ...form, event_date: e.target.value })}
        />
        <textarea
          className="rounded-md bg-slate-800 p-2"
          placeholder="Mô tả"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <button type="submit" className="rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-100">Thêm sự kiện</button>
      </form>
      {loading ? (
        <div className="text-sm text-slate-500">Đang tải...</div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
              <div className="font-medium">{item.title}</div>
              <div className="text-xs text-slate-400">{item.event_date || item.relative_order || ''}</div>
              {item.description && <div className="mt-1 text-sm text-slate-300">{item.description}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
