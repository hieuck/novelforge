import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

export default function Lore() {
  const { projectId } = useParams()
  const [items, setItems] = useState<{id: string; name: string; lore_type: string; description?: string}[]>([])
  const [form, setForm] = useState({ lore_type: 'location', name: '', description: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetch(`/api/projects/${projectId}/lore`)
      .then((r) => r.json())
      .then(setItems)
      .finally(() => setLoading(false))
  }, [projectId])

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetch(`/api/projects/${projectId}/lore`)
      .then((r) => r.json())
      .then(setItems)
      .finally(() => setLoading(false))
  }, [projectId])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectId) return
    const payload = { ...form, project_id: projectId }
    const res = await fetch('/api/lore', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (res.ok) {
      setForm({ lore_type: form.lore_type, name: '', description: '' })
      const r = await fetch(`/api/projects/${projectId}/lore`)
      setItems(await r.json())
    }
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-2xl font-bold">Worldbuilding / Lore</h1>
      <form onSubmit={submit} className="mb-6 grid gap-3 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <input
          className="rounded-md bg-slate-800 p-2"
          placeholder="Loại lore"
          value={form.lore_type}
          onChange={(e) => setForm({ ...form, lore_type: e.target.value })}
        />
        <input
          className="rounded-md bg-slate-800 p-2"
          placeholder="Tên"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <textarea
          className="rounded-md bg-slate-800 p-2"
          placeholder="Mô tả"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <button type="submit" className="rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-100">Thêm lore</button>
      </form>
      {loading ? (
        <div className="text-sm text-slate-500">Đang tải...</div>
      ) : (
        <div className="grid gap-3">
          {items.map((item) => (
            <div key={item.id} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
              <div className="font-medium">{item.name}</div>
              <div className="text-xs text-slate-400">{item.lore_type}</div>
              {item.description && <div className="mt-1 text-sm text-slate-300">{item.description}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
