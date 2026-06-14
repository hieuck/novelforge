import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams } from 'react-router-dom'
import { Plus, X, ChevronDown, ChevronUp, Trash2, Edit2, Check } from 'lucide-react'
import { api } from '../lib/api'
import type { Character } from '../types'

const EMPTY: Omit<Character, 'id' | 'project_id' | 'created_at' | 'updated_at'> = {
  name: '', alias: '', gender: '', role: '', age: '', personality: '', appearance: '',
  goals: '', secrets: '', first_appearance: '', notes: '',
}

export default function Characters() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const [list, setList] = useState<Character[]>([])
  const [form, setForm] = useState({ ...EMPTY })
  const [showForm, setShowForm] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ ...EMPTY })
  const [loading, setLoading] = useState(false)
  const [showAgent, setShowAgent] = useState(false)

  const load = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const data = await api.get<Character[]>(`/projects/${projectId}/characters`)
      setList(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [projectId])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim() || !projectId) return
    await api.post('/characters/', { project_id: projectId, ...form })
    setForm({ ...EMPTY })
    setShowForm(false)
    load()
  }

  const remove = async (id: string) => {
    if (!confirm(t('characters.delete_confirm'))) return
    await api.delete(`/characters/${id}`)
    setList((l) => l.filter((c) => c.id !== id))
  }

  const startEdit = (c: Character) => {
    setEditId(c.id)
    setEditForm({
      name: c.name, alias: c.alias ?? '', role: c.role ?? '', age: c.age ?? '',
      personality: c.personality ?? '', appearance: c.appearance ?? '',
      goals: c.goals ?? '', secrets: c.secrets ?? '',
      first_appearance: c.first_appearance ?? '', notes: c.notes ?? '',
    })
  }

  const saveEdit = async (id: string) => {
    await api.patch(`/characters/${id}`, editForm)
    setEditId(null)
    load()
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <h1 className="text-lg font-semibold text-slate-100">{t('characters.page_title')}</h1>
        <div className="flex items-center gap-2">

          <button
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            {t('characters.add')}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {showForm && (
          <form onSubmit={create} className="mb-4 rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-300">{t('characters.new_heading')}</span>
              <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-slate-300">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {(['name', 'gender', 'alias', 'role', 'age', 'first_appearance'] as const).map((f) => (
                <input
                  key={f}
                  className="rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                  placeholder={f === 'name' ? t('characters.field_name') : f === 'gender' ? t('characters.field_gender') : f === 'alias' ? t('characters.field_alias') : f === 'role' ? t('characters.field_role') : f === 'age' ? t('characters.field_age') : t('characters.field_first_appearance')}
                  required={f === 'name'}
                  value={form[f] ?? ''}
                  onChange={(e) => setForm({ ...form, [f]: e.target.value })}
                />
              ))}
            </div>
            {(['personality', 'appearance', 'goals', 'secrets', 'notes'] as const).map((f) => (
              <textarea
                key={f}
                rows={2}
                className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                placeholder={f === 'personality' ? t('characters.field_personality') : f === 'appearance' ? t('characters.field_appearance') : f === 'goals' ? t('characters.field_goals') : f === 'secrets' ? t('characters.field_secrets') : t('characters.field_notes')}
                value={form[f]}
                onChange={(e) => setForm({ ...form, [f]: e.target.value })}
              />
            ))}
            <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
              {t('characters.save')}
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-sm text-slate-500">{t('characters.loading')}</div>
        ) : (
          <div className="space-y-2">
            {list.map((c) => (
              <div key={c.id} className="rounded-lg border border-slate-800 bg-slate-900">
                <div
                  className="flex cursor-pointer items-center justify-between px-4 py-3"
                  onClick={() => setExpandedId(expandedId === c.id ? null : c.id)}
                >
                  <div>
                    <span className="font-medium text-slate-100">{c.name}</span>
                    {c.alias && <span className="ml-2 text-sm text-slate-500">({c.alias})</span>}
                    {c.role && <span className="ml-2 text-xs text-indigo-400">{c.role}</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={(e) => { e.stopPropagation(); startEdit(c) }} className="p-1 text-slate-600 hover:text-slate-300">
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); remove(c.id) }} className="p-1 text-slate-600 hover:text-red-400">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                    {expandedId === c.id ? <ChevronUp className="h-4 w-4 text-slate-500" /> : <ChevronDown className="h-4 w-4 text-slate-500" />}
                  </div>
                </div>

                {expandedId === c.id && (
                  <div className="border-t border-slate-800 px-4 pb-4 pt-3">
                    {editId === c.id ? (
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          {(['name','alias','role','age','first_appearance'] as const).map((f) => (
                            <input key={f}
                              className="rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                              value={editForm[f]}
                              onChange={(e) => setEditForm({ ...editForm, [f]: e.target.value })}
                              placeholder={f}
                            />
                          ))}
                        </div>
                        {(['personality','appearance','goals','secrets','notes'] as const).map((f) => (
                          <textarea key={f} rows={2}
                            className="w-full rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                            value={editForm[f]}
                            onChange={(e) => setEditForm({ ...editForm, [f]: e.target.value })}
                            placeholder={f}
                          />
                        ))}
                        <div className="flex gap-2">
                          <button onClick={() => saveEdit(c.id)} className="flex items-center gap-1 rounded bg-indigo-600 px-3 py-1.5 text-xs text-white hover:bg-indigo-700">
                            <Check className="h-3 w-3" /> {t('characters.save_edit')}
                          </button>
                          <button onClick={() => setEditId(null)} className="rounded border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200">
                            {t('characters.cancel_edit')}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                        {c.age && <Field label={t('characters.label_age')} value={c.age} />}
                        {c.first_appearance && <Field label={t('characters.label_first_appearance')} value={c.first_appearance} />}
                        {c.personality && <Field label={t('characters.field_personality')} value={c.personality} full />}
                        {c.appearance && <Field label={t('characters.field_appearance')} value={c.appearance} full />}
                        {c.goals && <Field label={t('characters.field_goals')} value={c.goals} full />}
                        {c.secrets && <Field label={t('characters.field_secrets')} value={c.secrets} full />}
                        {c.notes && <Field label={t('characters.field_notes')} value={c.notes} full />}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {!list.length && <div className="text-sm text-slate-500">{t('characters.empty_state')}</div>}
          </div>
        )}
      </div>
      </div>{/* end main content */}
    </div>
  )
}

function Field({ label, value, full }: { label: string; value: string; full?: boolean }) {
  return (
    <div className={full ? 'col-span-2' : ''}>
      <div className="text-[10px] uppercase tracking-wide text-slate-600">{label}</div>
      <div className="text-slate-300">{value}</div>
    </div>
  )
}
