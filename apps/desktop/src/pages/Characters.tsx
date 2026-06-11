import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

export default function Characters() {
  const { projectId } = useParams()
  const [list, setList] = useState<any[]>([])
  const [form, setForm] = useState({ name: '', role: '', bio: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetch(`/api/projects/${projectId}/characters`)
      .then((r) => r.json())
      .then(setList)
      .finally(() => setLoading(false))
  }, [projectId])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectId) return
    await fetch('/api/characters', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, ...form }),
    })
    setForm({ name: '', role: '', bio: '' })
    const r = await fetch(`/api/projects/${projectId}/characters`)
    setList(await r.json())
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-4 text-2xl font-bold">Character Bible</h1>
      <form onSubmit={submit} className="mb-6 grid gap-3 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <input
          className="rounded-md bg-slate-800 p-2"
          placeholder="Tên nhân vật"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          className="rounded-md bg-slate-800 p-2"
          placeholder="Vai trò"
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
        />
        <textarea
          className="rounded-md bg-slate-800 p-2"
          placeholder="Tiểu sử / đặc điểm"
          value={form.bio}
          onChange={(e) => setForm({ ...form, bio: e.target.value })}
        />
        <button type="submit" className="rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-100">
          Thêm nhân vật
        </button>
      </form>
      {loading ? (
        <div className="text-sm text-slate-500">Đang tải...</div>
      ) : (
        <div className="grid gap-3">
          {list.map((c) => (
            <div key={c.id} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <div className="font-medium">{c.name}</div>
              {c.role && <div className="text-xs text-slate-400">{c.role}</div>}
              {c.bio && <div className="mt-1 text-sm text-slate-300">{c.bio}</div>}
            </div>
          ))}
          {!list.length && <div className="text-sm text-slate-500">Chưa có nhân vật nào.</div>}
        </div>
      )}
    </div>
  )
}
