import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams } from 'react-router-dom'
import { Plus, Trash2, X, Edit2, Check, Bot } from 'lucide-react'
import { api } from '../lib/api'
import type { TimelineEvent } from '../types'
import AgentPanel from '../components/AgentPanel'

const EMPTY = { title: '', event_date: '', description: '', relative_order: '' }

export default function Timeline() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const [items, setItems] = useState<TimelineEvent[]>([])
  const [form, setForm] = useState({ ...EMPTY })
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ ...EMPTY })
  const [loading, setLoading] = useState(false)
  const [showAgent, setShowAgent] = useState(false)

  const load = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const data = await api.get<TimelineEvent[]>(`/projects/${projectId}/timeline`)
      setItems(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [projectId])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.title.trim() || !projectId) return
    await api.post('/timeline/', { project_id: projectId, ...form })
    setForm({ ...EMPTY })
    setShowForm(false)
    load()
  }

  const remove = async (id: string) => {
    if (!confirm(t('timeline.delete_confirm'))) return
    await api.delete(`/timeline/${id}`)
    setItems((l) => l.filter((x) => x.id !== id))
  }

  const saveEdit = async (id: string) => {
    await api.patch(`/timeline/${id}`, editForm)
    setEditId(null)
    load()
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <h1 className="text-lg font-semibold text-slate-100">{t('timeline.page_title')}</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAgent((v) => !v)}
            title={t('timeline.ai_tooltip')}
            className={`flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm transition-colors ${
              showAgent
                ? 'border-indigo-700 bg-indigo-900/40 text-indigo-300'
                : 'border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
            }`}
          >
            <Bot className="h-3.5 w-3.5" />
            {t('timeline.agent_toggle')}
          </button>
          <button
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            {t('timeline.add')}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {showForm && (
          <form onSubmit={create} className="mb-4 rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-300">{t('timeline.new_heading')}</span>
              <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-slate-300">
                <X className="h-4 w-4" />
              </button>
            </div>
            <input
              required
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
              placeholder={t('timeline.field_title')}
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                className="rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                placeholder={t('timeline.field_date')}
                value={form.event_date}
                onChange={(e) => setForm({ ...form, event_date: e.target.value })}
              />
              <input
                className="rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                placeholder={t('timeline.field_order')}
                value={form.relative_order}
                onChange={(e) => setForm({ ...form, relative_order: e.target.value })}
              />
            </div>
            <textarea
              rows={3}
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
              placeholder={t('timeline.field_description')}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
              {t('timeline.save_event')}
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-sm text-slate-500">{t('timeline.loading')}</div>
        ) : (
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-slate-800" />
            <div className="space-y-4 pl-10">
              {items.map((item, idx) => (
                <div key={item.id} className="relative">
                  <div className="absolute -left-6 mt-1 h-3 w-3 rounded-full border-2 border-indigo-500 bg-slate-950" />
                  <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
                    {editId === item.id ? (
                      <div className="space-y-2">
                        <input
                          className="w-full rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                          value={editForm.title}
                          onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                        />
                        <div className="grid grid-cols-2 gap-2">
                          <input
                            className="rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                            value={editForm.event_date}
                            onChange={(e) => setEditForm({ ...editForm, event_date: e.target.value })}
                            placeholder={t('timeline.field_date')}
                          />
                          <input
                            className="rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                            value={editForm.relative_order}
                            onChange={(e) => setEditForm({ ...editForm, relative_order: e.target.value })}
                            placeholder={t('timeline.field_order')}
                          />
                        </div>
                        <textarea rows={2}
                          className="w-full rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                          value={editForm.description}
                          onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                        />
                        <div className="flex gap-2">
                          <button onClick={() => saveEdit(item.id)} className="flex items-center gap-1 rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">
                            <Check className="h-3 w-3" /> {t('timeline.save_edit')}
                          </button>
                          <button onClick={() => setEditId(null)} className="rounded border border-slate-700 px-3 py-1 text-xs text-slate-400">{t('timeline.cancel_edit')}</button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-medium text-slate-100">{item.title}</div>
                            {(item.event_date || item.relative_order) && (
                              <div className="mt-0.5 text-xs text-indigo-400">
                                {item.event_date || item.relative_order}
                              </div>
                            )}
                          </div>
                          <div className="flex gap-1.5">
                            <button onClick={() => { setEditId(item.id); setEditForm({ title: item.title, event_date: item.event_date ?? '', description: item.description ?? '', relative_order: item.relative_order ?? '' }) }} className="p-1 text-slate-600 hover:text-slate-300">
                              <Edit2 className="h-3.5 w-3.5" />
                            </button>
                            <button onClick={() => remove(item.id)} className="p-1 text-slate-600 hover:text-red-400">
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>
                        {item.description && (
                          <div className="mt-2 text-sm text-slate-400 leading-relaxed">{item.description}</div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              ))}
              {!items.length && <div className="text-sm text-slate-500 pl-0">{t('timeline.empty_state')}</div>}
            </div>
          </div>
        )}
      </div>
      </div>{/* end main content */}

      {/* Agent panel */}
      {showAgent && (
        <div className="border-l border-slate-800">
          <AgentPanel projectId={projectId} />
        </div>
      )}
    </div>
  )
}
