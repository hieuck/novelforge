import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams } from 'react-router-dom'
import { Plus, Trash2, X, Edit2, Check } from 'lucide-react'
import { api } from '../lib/api'
import type { LoreItem } from '../types'
import AgentPanel from '../components/AgentPanel'

const LORE_TYPES = ['location', 'organization', 'rule', 'magic', 'technology', 'term', 'other']

const EMPTY = { lore_type: 'location', name: '', description: '', tags: '' }

export default function Lore() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const [items, setItems] = useState<LoreItem[]>([])
  const [filter, setFilter] = useState('all')
  const [form, setForm] = useState({ ...EMPTY })
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ ...EMPTY })
  const [loading, setLoading] = useState(false)

  const load = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const data = await api.get<LoreItem[]>(`/projects/${projectId}/lore`)
      setItems(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [projectId])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim() || !projectId) return
    await api.post('/lore/', {
      project_id: projectId,
      lore_type: form.lore_type,
      name: form.name,
      description: form.description,
      tags: form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
    })
    setForm({ ...EMPTY })
    setShowForm(false)
    load()
  }

  const remove = async (id: string) => {
    if (!confirm(t('lore.delete_confirm'))) return
    await api.delete(`/lore/${id}`)
    setItems((l) => l.filter((x) => x.id !== id))
  }

  const saveEdit = async (id: string) => {
    await api.patch(`/lore/${id}`, {
      lore_type: editForm.lore_type,
      name: editForm.name,
      description: editForm.description,
      tags: editForm.tags ? editForm.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
    })
    setEditId(null)
    load()
  }

  const filtered = filter === 'all' ? items : items.filter((i) => i.lore_type === filter)

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <h1 className="text-lg font-semibold text-slate-100">{t('lore.page_title')}</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            {t('lore.add')}
          </button>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto border-b border-slate-800 px-6 py-2">
        <button
          onClick={() => setFilter('all')}
          className={`rounded-full px-3 py-1 text-xs ${filter === 'all' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'}`}
        >
          {t('lore.filter_all')}
        </button>
        {LORE_TYPES.map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`rounded-full px-3 py-1 text-xs capitalize ${filter === t ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'}`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {showForm && (
          <form onSubmit={create} className="mb-4 rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-slate-300">{t('lore.new_heading')}</span>
              <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-slate-300">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <select
                className="rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 focus:border-indigo-600 focus:outline-none"
                value={form.lore_type}
                onChange={(e) => setForm({ ...form, lore_type: e.target.value })}
              >
                {LORE_TYPES.map((t) => <option key={t} value={t} className="capitalize">{t}</option>)}
              </select>
              <input
                required
                className="rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                placeholder={t('lore.field_name')}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <textarea
              rows={3}
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
              placeholder={t('lore.field_description')}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <input
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
              placeholder={t('lore.field_tags')}
              value={form.tags}
              onChange={(e) => setForm({ ...form, tags: e.target.value })}
            />
            <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
              {t('lore.save')}
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-sm text-slate-500">{t('lore.loading')}</div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {filtered.map((item) => (
              <div key={item.id} className="rounded-lg border border-slate-800 bg-slate-900 p-4">
                {editId === item.id ? (
                  <div className="space-y-2">
                    <div className="grid grid-cols-2 gap-2">
                      <select
                        className="rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                        value={editForm.lore_type}
                        onChange={(e) => setEditForm({ ...editForm, lore_type: e.target.value })}
                      >
                        {LORE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                      </select>
                      <input
                        className="rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      />
                    </div>
                    <textarea rows={3}
                      className="w-full rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                      value={editForm.description}
                      onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    />
                    <input
                      className="w-full rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                      value={editForm.tags}
                      onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                      placeholder={t('lore.field_tags')}
                    />
                    <div className="flex gap-2">
                      <button onClick={() => saveEdit(item.id)} className="flex items-center gap-1 rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">
                        <Check className="h-3 w-3" /> {t('lore.save_edit')}
                      </button>
                      <button onClick={() => setEditId(null)} className="rounded border border-slate-700 px-3 py-1 text-xs text-slate-400">{t('lore.cancel_edit')}</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium text-slate-100">{item.name}</div>
                        <span className="text-[10px] uppercase text-indigo-400">{item.lore_type}</span>
                      </div>
                      <div className="flex gap-1.5">
                        <button onClick={() => { setEditId(item.id); setEditForm({ lore_type: item.lore_type, name: item.name, description: item.description ?? '', tags: (item.tags ?? []).join(', ') }) }} className="p-1 text-slate-600 hover:text-slate-300">
                          <Edit2 className="h-3.5 w-3.5" />
                        </button>
                        <button onClick={() => remove(item.id)} className="p-1 text-slate-600 hover:text-red-400">
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                    {item.description && <div className="mt-2 text-sm text-slate-400 leading-relaxed">{item.description}</div>}
                    {item.tags && item.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {item.tags.map((t) => (
                          <span key={t} className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">{t}</span>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
            {!filtered.length && <div className="text-sm text-slate-500 col-span-2">{t('lore.empty_state')}</div>}
          </div>
        )}
      </div>
      </div>{/* end main content */}
    </div>
  )
}
