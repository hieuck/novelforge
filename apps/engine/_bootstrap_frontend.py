"""Write all frontend source files."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "desktop" / "src"

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"  wrote {rel}")


# ── lib/api.ts ────────────────────────────────────────────────────────────────
w("lib/api.ts", """
const BASE = '/api'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'content-type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Request failed')
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => req<T>(path),
  post: <T>(path: string, body: unknown) =>
    req<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    req<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path: string) => req<void>(path, { method: 'DELETE' }),
}

export function wsUrl(path: string): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const port = (window as any).__VITE_ENGINE_PORT__ ?? '9000'
  return `${proto}//127.0.0.1:${port}/api${path}`
}
""")

# ── types/index.ts ─────────────────────────────────────────────────────────────
w("types/index.ts", """
export interface Project {
  id: string
  title: string
  description?: string
  genre?: string
  language?: string
  style_guide?: string
  summary?: string
  created_at?: string
  updated_at?: string
}

export interface Chapter {
  id: string
  project_id: string
  title: string
  content?: string
  word_count?: number
  status?: string
  scene_order?: number
  summary?: string
  notes?: string
  created_at?: string
  updated_at?: string
}

export interface Character {
  id: string
  project_id: string
  name: string
  alias?: string
  role?: string
  age?: string
  personality?: string
  appearance?: string
  goals?: string
  secrets?: string
  relationships?: Record<string, string>
  first_appearance?: string
  notes?: string
  summary?: string
  created_at?: string
  updated_at?: string
}

export interface LoreItem {
  id: string
  project_id: string
  lore_type: string
  name: string
  description?: string
  tags?: string[]
  related_chapters?: string[]
  related_characters?: string[]
  metadata?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export interface TimelineEvent {
  id: string
  project_id: string
  title: string
  event_date?: string
  relative_order?: string
  description?: string
  involved_characters?: string[]
  related_chapters?: string[]
  metadata?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export interface AISettings {
  provider: string
  base_url: string
  api_key?: string
  model: string
  temperature: number
  max_tokens: number
}

export const AI_ACTIONS = [
  { value: 'continue',          label: 'Tiếp tục viết' },
  { value: 'rewrite',           label: 'Viết lại' },
  { value: 'expand',            label: 'Mở rộng' },
  { value: 'shorten',           label: 'Rút gọn' },
  { value: 'dialogue',          label: 'Cải thiện hội thoại' },
  { value: 'emotional',         label: 'Tăng cảm xúc' },
  { value: 'cinematic',         label: 'Điện ảnh hóa' },
  { value: 'grammar',           label: 'Sửa ngữ pháp' },
  { value: 'summarize_chapter', label: 'Tóm tắt chương' },
  { value: 'summarize_project', label: 'Tóm tắt project' },
  { value: 'continuity',        label: 'Kiểm tra nhất quán' },
  { value: 'plot_holes',        label: 'Tìm plot holes' },
  { value: 'next_scene',        label: 'Gợi ý cảnh tiếp' },
  { value: 'character',         label: 'Tạo nhân vật' },
  { value: 'world',             label: 'Tạo lore' },
  { value: 'premise',           label: 'Tạo premise' },
  { value: 'outline',           label: 'Tạo dàn ý' },
  { value: 'translate_vi_en',   label: 'Dịch VI → EN' },
  { value: 'translate_en_vi',   label: 'Dịch EN → VI' },
] as const

export type AIAction = typeof AI_ACTIONS[number]['value']
""")

# ── stores/projectStore.ts ─────────────────────────────────────────────────────
w("stores/projectStore.ts", """
import { create } from 'zustand'
import { api } from '../lib/api'
import type { Project } from '../types'

interface ProjectStore {
  projects: Project[]
  activeProjectId?: string
  setActiveProject: (id: string) => void
  fetchProjects: () => Promise<void>
  createProject: (values: Partial<Project>) => Promise<Project>
  updateProject: (id: string, values: Partial<Project>) => Promise<Project>
  deleteProject: (id: string) => Promise<void>
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  activeProjectId: undefined,

  setActiveProject: (id) => set({ activeProjectId: id }),

  fetchProjects: async () => {
    const data = await api.get<Project[]>('/projects/')
    set({ projects: Array.isArray(data) ? data : [] })
  },

  createProject: async (values) => {
    const data = await api.post<Project>('/projects/', values)
    set((s) => ({ projects: [data, ...s.projects] }))
    return data
  },

  updateProject: async (id, values) => {
    const data = await api.patch<Project>(`/projects/${id}`, values)
    set((s) => ({ projects: s.projects.map((p) => (p.id === id ? data : p)) }))
    return data
  },

  deleteProject: async (id) => {
    await api.delete(`/projects/${id}`)
    set((s) => ({ projects: s.projects.filter((p) => p.id !== id) }))
  },
}))
""")

# ── stores/chapterStore.ts ────────────────────────────────────────────────────
w("stores/chapterStore.ts", """
import { create } from 'zustand'
import { api } from '../lib/api'
import type { Chapter } from '../types'

interface ChapterStore {
  chapters: Chapter[]
  activeChapterId?: string
  setActiveChapter: (id?: string) => void
  fetchChapters: (projectId: string) => Promise<void>
  createChapter: (values: Partial<Chapter>) => Promise<Chapter>
  updateChapter: (id: string, values: Partial<Chapter>) => Promise<void>
  deleteChapter: (id: string) => Promise<void>
}

export const useChapterStore = create<ChapterStore>((set, get) => ({
  chapters: [],
  activeChapterId: undefined,

  setActiveChapter: (id) => set({ activeChapterId: id }),

  fetchChapters: async (projectId) => {
    const data = await api.get<Chapter[]>(`/projects/${projectId}/chapters`)
    set({ chapters: Array.isArray(data) ? data : [] })
  },

  createChapter: async (values) => {
    const data = await api.post<Chapter>('/chapters/', values)
    set((s) => ({ chapters: [...s.chapters, data] }))
    return data
  },

  updateChapter: async (id, values) => {
    const data = await api.patch<Chapter>(`/chapters/${id}`, values)
    set((s) => ({
      chapters: s.chapters.map((c) => (c.id === id ? { ...c, ...data } : c)),
    }))
  },

  deleteChapter: async (id) => {
    await api.delete(`/chapters/${id}`)
    set((s) => ({
      chapters: s.chapters.filter((c) => c.id !== id),
      activeChapterId: get().activeChapterId === id ? undefined : get().activeChapterId,
    }))
  },
}))
""")

# ── stores/settingsStore.ts ───────────────────────────────────────────────────
w("stores/settingsStore.ts", """
import { create } from 'zustand'
import { api } from '../lib/api'
import type { AISettings } from '../types'

interface SettingsStore {
  settings: AISettings
  loaded: boolean
  fetchSettings: () => Promise<void>
  saveSettings: (values: AISettings) => Promise<{ ok: boolean; error?: string }>
  testConnection: (values: AISettings) => Promise<{ ok: boolean; response?: string; error?: string }>
}

const defaults: AISettings = {
  provider: 'ollama',
  base_url: 'http://localhost:11434',
  api_key: '',
  model: 'llama3.1:8b',
  temperature: 0.7,
  max_tokens: 2048,
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: defaults,
  loaded: false,

  fetchSettings: async () => {
    try {
      const data = await api.get<AISettings>('/settings/current')
      set({ settings: { ...defaults, ...data }, loaded: true })
    } catch {
      set({ loaded: true })
    }
  },

  saveSettings: async (values) => {
    try {
      const data = await api.post<AISettings>('/settings/current', values)
      set({ settings: { ...defaults, ...data } })
      return { ok: true }
    } catch (e: any) {
      return { ok: false, error: e.message }
    }
  },

  testConnection: async (values) => {
    try {
      const data = await api.post<{ ok: boolean; response?: string; error?: string }>(
        '/settings/test', values
      )
      return data
    } catch (e: any) {
      return { ok: false, error: e.message }
    }
  },
}))
""")

# ── stores/aiStore.ts ─────────────────────────────────────────────────────────
w("components/AiPanel.tsx", """
import { create } from 'zustand'
import { api } from '../lib/api'
import type { AIAction } from '../types'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}

interface AIMeta {
  projectId?: string
  chapterId?: string
  action?: AIAction
  instruction?: string
}

interface AIStore {
  messages: Message[]
  loading: boolean
  clearMessages: () => void
  sendMessage: (text: string, meta?: AIMeta) => Promise<void>
}

export const useAiStore = create<AIStore>((set, get) => ({
  messages: [],
  loading: false,

  clearMessages: () => set({ messages: [] }),

  sendMessage: async (text, meta = {}) => {
    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      createdAt: new Date().toISOString(),
    }
    set((s) => ({ messages: [...s.messages, userMsg], loading: true }))

    try {
      const res = await api.post<{ result: string; action: string }>('/ai/run', {
        project_id: meta.projectId ?? null,
        chapter_id: meta.chapterId ?? null,
        action: meta.action ?? 'continue',
        text,
        instruction: meta.instruction ?? '',
      })
      const assistantMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: res.result ?? '[no response]',
        createdAt: new Date().toISOString(),
      }
      set((s) => ({ messages: [...s.messages, assistantMsg] }))
    } catch (e: any) {
      const errMsg: Message = {
        id: `e-${Date.now()}`,
        role: 'assistant',
        content: `Lỗi: ${e.message ?? 'Không kết nối được AI'}`,
        createdAt: new Date().toISOString(),
      }
      set((s) => ({ messages: [...s.messages, errMsg] }))
    } finally {
      set({ loading: false })
    }
  },
}))
""")

# ── components/Sidebar.tsx ────────────────────────────────────────────────────
w("components/Sidebar.tsx", """
import { useEffect } from 'react'
import { NavLink, useParams } from 'react-router-dom'
import { BookOpen, Settings, LayoutDashboard, Users, Globe, Clock, FileText } from 'lucide-react'
import { useProjectStore } from '../stores/projectStore'

export default function Sidebar() {
  const { projects, fetchProjects } = useProjectStore()
  const { projectId } = useParams()

  useEffect(() => { fetchProjects() }, [])

  const navCls = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
      isActive ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
    }`

  return (
    <aside className="flex h-full w-56 flex-col border-r border-slate-800 bg-slate-950">
      <header className="border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-bold text-slate-100">NovelForge</span>
        </div>
        <div className="mt-0.5 text-[11px] text-slate-500">Offline writing studio</div>
      </header>

      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        <NavLink to="/" end className={navCls}>
          <LayoutDashboard className="h-4 w-4" />
          Dashboard
        </NavLink>

        {projectId && (
          <>
            <div className="mt-3 px-3 pb-1 text-[10px] uppercase tracking-wider text-slate-600">
              Project
            </div>
            <NavLink to={`/projects/${projectId}/chapters`} className={navCls}>
              <FileText className="h-4 w-4" />
              Chapters
            </NavLink>
            <NavLink to={`/projects/${projectId}/characters`} className={navCls}>
              <Users className="h-4 w-4" />
              Characters
            </NavLink>
            <NavLink to={`/projects/${projectId}/lore`} className={navCls}>
              <Globe className="h-4 w-4" />
              Lore
            </NavLink>
            <NavLink to={`/projects/${projectId}/timeline`} className={navCls}>
              <Clock className="h-4 w-4" />
              Timeline
            </NavLink>
          </>
        )}

        {projects.length > 0 && (
          <>
            <div className="mt-3 px-3 pb-1 text-[10px] uppercase tracking-wider text-slate-600">
              Projects
            </div>
            {projects.map((p) => (
              <NavLink
                key={p.id}
                to={`/projects/${p.id}/chapters`}
                className={({ isActive }) =>
                  `block rounded-md px-3 py-2 text-sm transition-colors ${
                    isActive || p.id === projectId
                      ? 'bg-slate-800 text-slate-100'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`
                }
              >
                <div className="truncate font-medium">{p.title}</div>
                {p.genre && <div className="text-[10px] text-slate-500">{p.genre}</div>}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <footer className="border-t border-slate-800 px-2 py-2">
        <NavLink to="/settings" className={navCls}>
          <Settings className="h-4 w-4" />
          Settings
        </NavLink>
      </footer>
    </aside>
  )
}
""")

# ── components/AiPanel.tsx ────────────────────────────────────────────────────
w("components/AiPanel.tsx", """
import { useRef, useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Send, Trash2, Bot } from 'lucide-react'
import { useAiStore } from '../stores/aiStore'
import { useChapterStore } from '../stores/chapterStore'
import { AI_ACTIONS } from '../types'
import type { AIAction } from '../types'

export default function AiPanel() {
  const { projectId } = useParams()
  const { messages, loading, sendMessage, clearMessages } = useAiStore()
  const { activeChapterId } = useChapterStore()
  const [input, setInput] = useState('')
  const [action, setAction] = useState<AIAction>('continue')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    await sendMessage(text, {
      projectId,
      chapterId: activeChapterId,
      action,
    })
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      submit(e as any)
    }
  }

  return (
    <aside className="flex h-full w-80 flex-col border-l border-slate-800 bg-slate-950">
      <header className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-semibold text-slate-200">AI Assistant</span>
        </div>
        <button
          onClick={clearMessages}
          title="Clear chat"
          className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </header>

      {/* Action selector */}
      <div className="border-b border-slate-800 px-3 py-2">
        <select
          value={action}
          onChange={(e) => setAction(e.target.value as AIAction)}
          className="w-full rounded-md border border-slate-800 bg-slate-900 px-2 py-1.5 text-xs text-slate-300"
        >
          {AI_ACTIONS.map((a) => (
            <option key={a.value} value={a.value}>{a.label}</option>
          ))}
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        {messages.length === 0 && (
          <div className="mt-4 text-center text-xs text-slate-600">
            Chọn action, nhập yêu cầu và nhấn Ctrl+Enter
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`rounded-lg p-3 text-sm ${
              m.role === 'user'
                ? 'bg-slate-800 text-slate-100'
                : 'bg-slate-900 text-slate-200 border border-slate-800'
            }`}
          >
            <div className="mb-1 text-[10px] text-slate-500 uppercase tracking-wide">
              {m.role === 'user' ? 'Bạn' : 'AI'}
            </div>
            <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
          </div>
        ))}
        {loading && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <div className="text-[10px] text-slate-500 mb-1">AI</div>
            <div className="flex gap-1">
              {[0,1,2].map(i => (
                <span
                  key={i}
                  className="inline-block h-1.5 w-1.5 rounded-full bg-indigo-400 animate-bounce"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={submit} className="border-t border-slate-800 p-3 space-y-2">
        <textarea
          className="h-20 w-full resize-none rounded-md border border-slate-800 bg-slate-900 p-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-700 focus:outline-none"
          placeholder="Nhập yêu cầu... (Ctrl+Enter để gửi)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
        >
          <Send className="h-3.5 w-3.5" />
          {loading ? 'Đang xử lý...' : 'Gửi'}
        </button>
      </form>
    </aside>
  )
}
""")

# ── pages/Dashboard.tsx ───────────────────────────────────────────────────────
w("pages/Dashboard.tsx", """
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, BookOpen, Trash2 } from 'lucide-react'
import { useProjectStore } from '../stores/projectStore'

export default function Dashboard() {
  const { projects, fetchProjects, createProject, deleteProject } = useProjectStore()
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ title: '', genre: '', language: 'vi', description: '' })
  const [showForm, setShowForm] = useState(false)

  useEffect(() => { fetchProjects() }, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.title.trim()) return
    setCreating(true)
    try {
      const p = await createProject(form)
      setShowForm(false)
      setForm({ title: '', genre: '', language: 'vi', description: '' })
      navigate(`/projects/${p.id}/chapters`)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">NovelForge</h1>
          <p className="text-sm text-slate-400">Công cụ viết truyện offline với AI</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Tạo project mới
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={submit}
          className="mb-6 rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3"
        >
          <div className="text-sm font-semibold text-slate-200 mb-2">Project mới</div>
          <input
            autoFocus
            required
            className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-600 focus:outline-none"
            placeholder="Tên truyện *"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              className="rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-600 focus:outline-none"
              placeholder="Thể loại"
              value={form.genre}
              onChange={(e) => setForm({ ...form, genre: e.target.value })}
            />
            <select
              className="rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-indigo-600 focus:outline-none"
              value={form.language}
              onChange={(e) => setForm({ ...form, language: e.target.value })}
            >
              <option value="vi">Tiếng Việt</option>
              <option value="en">English</option>
            </select>
          </div>
          <textarea
            className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-600 focus:outline-none"
            placeholder="Mô tả ngắn..."
            rows={2}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={creating}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {creating ? 'Đang tạo...' : 'Tạo project'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-400 hover:border-slate-600 hover:text-slate-200"
            >
              Hủy
            </button>
          </div>
        </form>
      )}

      <div className="grid gap-3">
        {projects.map((p) => (
          <div
            key={p.id}
            className="group flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900 p-4 hover:border-slate-700 cursor-pointer"
            onClick={() => navigate(`/projects/${p.id}/chapters`)}
          >
            <div className="flex items-center gap-3">
              <BookOpen className="h-5 w-5 text-indigo-400 flex-shrink-0" />
              <div>
                <div className="font-medium text-slate-100">{p.title}</div>
                <div className="flex gap-2 mt-0.5">
                  {p.genre && <span className="text-xs text-slate-400">{p.genre}</span>}
                  {p.language && <span className="text-xs text-slate-600">{p.language}</span>}
                </div>
                {p.description && (
                  <div className="mt-1 text-xs text-slate-500 line-clamp-1">{p.description}</div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              {p.updated_at && (
                <span className="text-xs text-slate-600">
                  {new Date(p.updated_at).toLocaleDateString('vi-VN')}
                </span>
              )}
              <button
                onClick={(e) => { e.stopPropagation(); deleteProject(p.id) }}
                className="rounded p-1 text-slate-700 opacity-0 group-hover:opacity-100 hover:bg-slate-800 hover:text-red-400 transition-all"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {!projects.length && (
          <div className="rounded-lg border border-dashed border-slate-800 p-8 text-center">
            <BookOpen className="mx-auto h-8 w-8 text-slate-700 mb-2" />
            <div className="text-sm text-slate-500">Chưa có project nào.</div>
            <div className="text-xs text-slate-600 mt-1">Nhấn "Tạo project mới" để bắt đầu.</div>
          </div>
        )}
      </div>
    </div>
  )
}
""")

# ── pages/Chapters.tsx (Editor page) ─────────────────────────────────────────
w("pages/Chapters.tsx", """
import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Plus, Trash2, Save, CheckCircle } from 'lucide-react'
import { useChapterStore } from '../stores/chapterStore'
import AiPanel from '../components/AiPanel'

const STATUS_COLORS: Record<string, string> = {
  draft: 'text-slate-500',
  revised: 'text-yellow-500',
  final: 'text-green-500',
}

export default function Chapters() {
  const { projectId, chapterId } = useParams()
  const navigate = useNavigate()
  const { chapters, fetchChapters, createChapter, updateChapter, deleteChapter, setActiveChapter } =
    useChapterStore()

  const currentId = chapterId
  const chapter = chapters.find((c) => c.id === currentId)

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [status, setStatus] = useState('draft')
  const [saved, setSaved] = useState(true)
  const [saving, setSaving] = useState(false)
  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (projectId) fetchChapters(projectId)
  }, [projectId])

  useEffect(() => {
    if (chapter) {
      setTitle(chapter.title ?? '')
      setContent(chapter.content ?? '')
      setStatus(chapter.status ?? 'draft')
      setSaved(true)
      setActiveChapter(chapter.id)
    }
  }, [chapter?.id])

  // Autosave 1.5s after last keystroke
  const scheduleAutosave = useCallback(() => {
    setSaved(false)
    if (autosaveTimer.current) clearTimeout(autosaveTimer.current)
    autosaveTimer.current = setTimeout(() => {
      if (currentId) save(true)
    }, 1500)
  }, [currentId, title, content, status])

  const save = async (auto = false) => {
    if (!currentId) return
    if (!auto) setSaving(true)
    await updateChapter(currentId, { title, content, status })
    setSaved(true)
    if (!auto) setSaving(false)
  }

  const newChapter = async () => {
    if (!projectId) return
    const order = chapters.length
    const ch = await createChapter({
      project_id: projectId,
      title: `Chương ${order + 1}`,
      content: '',
      status: 'draft',
      scene_order: order,
    })
    navigate(`/projects/${projectId}/chapters/${ch.id}`)
  }

  const removeChapter = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Xóa chương này?')) return
    await deleteChapter(id)
    if (currentId === id) navigate(`/projects/${projectId}/chapters`)
  }

  const wordCount = content.split(/\\s+/).filter(Boolean).length

  return (
    <div className="flex h-full">
      {/* Chapter list */}
      <aside className="flex w-52 flex-col border-r border-slate-800 bg-slate-950">
        <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
          <span className="text-xs font-semibold text-slate-400">Chapters</span>
          <button
            onClick={newChapter}
            className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-200"
            title="New chapter"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-1">
          {chapters.map((ch) => (
            <div
              key={ch.id}
              onClick={() => navigate(`/projects/${projectId}/chapters/${ch.id}`)}
              className={`group flex cursor-pointer items-center justify-between px-3 py-2 ${
                ch.id === currentId ? 'bg-slate-800' : 'hover:bg-slate-900'
              }`}
            >
              <div className="min-w-0 flex-1">
                <div className={`truncate text-sm ${ch.id === currentId ? 'text-slate-100' : 'text-slate-400'}`}>
                  {ch.title || 'Untitled'}
                </div>
                <div className={`text-[10px] ${STATUS_COLORS[ch.status ?? 'draft'] ?? 'text-slate-600'}`}>
                  {ch.status} · {ch.word_count ?? 0}w
                </div>
              </div>
              <button
                onClick={(e) => removeChapter(ch.id, e)}
                className="ml-1 rounded p-0.5 text-slate-700 opacity-0 group-hover:opacity-100 hover:text-red-400"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))}
          {!chapters.length && (
            <div className="p-3 text-center text-xs text-slate-600">No chapters yet</div>
          )}
        </div>
      </aside>

      {/* Editor */}
      <div className="flex flex-1 flex-col min-w-0">
        {chapter ? (
          <>
            {/* Toolbar */}
            <div className="flex items-center gap-2 border-b border-slate-800 px-4 py-2">
              <input
                className="flex-1 bg-transparent text-lg font-semibold text-slate-100 placeholder:text-slate-600 outline-none"
                value={title}
                onChange={(e) => { setTitle(e.target.value); scheduleAutosave() }}
                placeholder="Chapter title"
              />
              <select
                className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-xs text-slate-300"
                value={status}
                onChange={(e) => { setStatus(e.target.value); scheduleAutosave() }}
              >
                <option value="draft">Draft</option>
                <option value="revised">Revised</option>
                <option value="final">Final</option>
              </select>
              <button
                onClick={() => save()}
                disabled={saved || saving}
                className="flex items-center gap-1.5 rounded-md border border-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 disabled:opacity-40"
              >
                {saved ? <CheckCircle className="h-3.5 w-3.5 text-green-500" /> : <Save className="h-3.5 w-3.5" />}
                {saving ? 'Saving...' : saved ? 'Saved' : 'Save'}
              </button>
            </div>

            {/* Text area */}
            <textarea
              className="flex-1 resize-none bg-transparent px-6 py-4 text-slate-200 leading-relaxed placeholder:text-slate-700 outline-none font-serif text-base"
              value={content}
              onChange={(e) => { setContent(e.target.value); scheduleAutosave() }}
              placeholder="Bắt đầu viết chương của bạn..."
            />

            {/* Status bar */}
            <div className="flex items-center justify-between border-t border-slate-800 px-4 py-1.5 text-xs text-slate-600">
              <span>{wordCount} từ</span>
              <span>{saved ? '✓ Đã lưu' : '● Chưa lưu'}</span>
            </div>
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 text-slate-600">
            <div className="text-sm">Chọn chương để chỉnh sửa</div>
            <button
              onClick={newChapter}
              className="flex items-center gap-2 rounded-md border border-slate-800 px-4 py-2 text-sm hover:border-slate-700 hover:text-slate-400"
            >
              <Plus className="h-4 w-4" />
              Tạo chương đầu tiên
            </button>
          </div>
        )}
      </div>

      {/* AI Panel */}
      <AiPanel />
    </div>
  )
}
""")

# ── pages/Characters.tsx ──────────────────────────────────────────────────────
w("pages/Characters.tsx", """
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Plus, X, ChevronDown, ChevronUp, Trash2, Edit2, Check } from 'lucide-react'
import { api } from '../lib/api'
import type { Character } from '../types'

const EMPTY: Omit<Character, 'id' | 'project_id' | 'created_at' | 'updated_at'> = {
  name: '', alias: '', role: '', age: '', personality: '', appearance: '',
  goals: '', secrets: '', first_appearance: '', notes: '',
}

export default function Characters() {
  const { projectId } = useParams()
  const [list, setList] = useState<Character[]>([])
  const [form, setForm] = useState({ ...EMPTY })
  const [showForm, setShowForm] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ ...EMPTY })
  const [loading, setLoading] = useState(false)

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
    if (!confirm('Xóa nhân vật này?')) return
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
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <h1 className="text-lg font-semibold text-slate-100">Character Bible</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Thêm nhân vật
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {showForm && (
          <form onSubmit={create} className="mb-4 rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-300">Nhân vật mới</span>
              <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-slate-300">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {(['name', 'alias', 'role', 'age', 'first_appearance'] as const).map((f) => (
                <input
                  key={f}
                  className="rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                  placeholder={f === 'name' ? 'Tên *' : f === 'alias' ? 'Bí danh' : f === 'role' ? 'Vai trò' : f === 'age' ? 'Tuổi' : 'Xuất hiện lần đầu'}
                  required={f === 'name'}
                  value={form[f]}
                  onChange={(e) => setForm({ ...form, [f]: e.target.value })}
                />
              ))}
            </div>
            {(['personality', 'appearance', 'goals', 'secrets', 'notes'] as const).map((f) => (
              <textarea
                key={f}
                rows={2}
                className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                placeholder={f === 'personality' ? 'Tính cách' : f === 'appearance' ? 'Ngoại hình' : f === 'goals' ? 'Mục tiêu' : f === 'secrets' ? 'Bí mật' : 'Ghi chú'}
                value={form[f]}
                onChange={(e) => setForm({ ...form, [f]: e.target.value })}
              />
            ))}
            <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
              Lưu nhân vật
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-sm text-slate-500">Đang tải...</div>
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
                            <Check className="h-3 w-3" /> Lưu
                          </button>
                          <button onClick={() => setEditId(null)} className="rounded border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200">
                            Hủy
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                        {c.age && <Field label="Tuổi" value={c.age} />}
                        {c.first_appearance && <Field label="Xuất hiện" value={c.first_appearance} />}
                        {c.personality && <Field label="Tính cách" value={c.personality} full />}
                        {c.appearance && <Field label="Ngoại hình" value={c.appearance} full />}
                        {c.goals && <Field label="Mục tiêu" value={c.goals} full />}
                        {c.secrets && <Field label="Bí mật" value={c.secrets} full />}
                        {c.notes && <Field label="Ghi chú" value={c.notes} full />}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {!list.length && <div className="text-sm text-slate-500">Chưa có nhân vật nào.</div>}
          </div>
        )}
      </div>
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
""")

# ── pages/Lore.tsx ─────────────────────────────────────────────────────────────
w("pages/Lore.tsx", """
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Plus, Trash2, X, Edit2, Check } from 'lucide-react'
import { api } from '../lib/api'
import type { LoreItem } from '../types'

const LORE_TYPES = ['location', 'organization', 'rule', 'magic', 'technology', 'term', 'other']

const EMPTY = { lore_type: 'location', name: '', description: '', tags: '' }

export default function Lore() {
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
    if (!confirm('Xóa lore item này?')) return
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
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <h1 className="text-lg font-semibold text-slate-100">Worldbuilding / Lore</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Thêm lore
        </button>
      </div>

      <div className="flex gap-2 overflow-x-auto border-b border-slate-800 px-6 py-2">
        <button
          onClick={() => setFilter('all')}
          className={`rounded-full px-3 py-1 text-xs ${filter === 'all' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'}`}
        >
          All
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
              <span className="text-sm font-medium text-slate-300">Lore mới</span>
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
                placeholder="Tên *"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <textarea
              rows={3}
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
              placeholder="Mô tả chi tiết..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <input
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
              placeholder="Tags (phân cách bằng dấu phẩy)"
              value={form.tags}
              onChange={(e) => setForm({ ...form, tags: e.target.value })}
            />
            <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
              Lưu
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-sm text-slate-500">Đang tải...</div>
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
                      placeholder="Tags"
                    />
                    <div className="flex gap-2">
                      <button onClick={() => saveEdit(item.id)} className="flex items-center gap-1 rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">
                        <Check className="h-3 w-3" /> Lưu
                      </button>
                      <button onClick={() => setEditId(null)} className="rounded border border-slate-700 px-3 py-1 text-xs text-slate-400">Hủy</button>
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
            {!filtered.length && <div className="text-sm text-slate-500 col-span-2">Chưa có lore nào.</div>}
          </div>
        )}
      </div>
    </div>
  )
}
""")

# ── pages/Timeline.tsx ─────────────────────────────────────────────────────────
w("pages/Timeline.tsx", """
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Plus, Trash2, X, Edit2, Check } from 'lucide-react'
import { api } from '../lib/api'
import type { TimelineEvent } from '../types'

const EMPTY = { title: '', event_date: '', description: '', relative_order: '' }

export default function Timeline() {
  const { projectId } = useParams()
  const [items, setItems] = useState<TimelineEvent[]>([])
  const [form, setForm] = useState({ ...EMPTY })
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ ...EMPTY })
  const [loading, setLoading] = useState(false)

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
    if (!confirm('Xóa sự kiện này?')) return
    await api.delete(`/timeline/${id}`)
    setItems((l) => l.filter((x) => x.id !== id))
  }

  const saveEdit = async (id: string) => {
    await api.patch(`/timeline/${id}`, editForm)
    setEditId(null)
    load()
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <h1 className="text-lg font-semibold text-slate-100">Timeline</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Thêm sự kiện
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {showForm && (
          <form onSubmit={create} className="mb-4 rounded-lg border border-slate-800 bg-slate-900 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-300">Sự kiện mới</span>
              <button type="button" onClick={() => setShowForm(false)} className="text-slate-500 hover:text-slate-300">
                <X className="h-4 w-4" />
              </button>
            </div>
            <input
              required
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
              placeholder="Tên sự kiện *"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                className="rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                placeholder="Ngày / thời điểm"
                value={form.event_date}
                onChange={(e) => setForm({ ...form, event_date: e.target.value })}
              />
              <input
                className="rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
                placeholder="Thứ tự (1, 2, 3...)"
                value={form.relative_order}
                onChange={(e) => setForm({ ...form, relative_order: e.target.value })}
              />
            </div>
            <textarea
              rows={3}
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
              placeholder="Mô tả sự kiện..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
              Lưu sự kiện
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-sm text-slate-500">Đang tải...</div>
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
                            placeholder="Ngày"
                          />
                          <input
                            className="rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                            value={editForm.relative_order}
                            onChange={(e) => setEditForm({ ...editForm, relative_order: e.target.value })}
                            placeholder="Thứ tự"
                          />
                        </div>
                        <textarea rows={2}
                          className="w-full rounded border border-slate-800 bg-slate-800 px-2 py-1 text-sm text-slate-200"
                          value={editForm.description}
                          onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                        />
                        <div className="flex gap-2">
                          <button onClick={() => saveEdit(item.id)} className="flex items-center gap-1 rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700">
                            <Check className="h-3 w-3" /> Lưu
                          </button>
                          <button onClick={() => setEditId(null)} className="rounded border border-slate-700 px-3 py-1 text-xs text-slate-400">Hủy</button>
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
              {!items.length && <div className="text-sm text-slate-500 pl-0">Chưa có sự kiện nào.</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
""")

# ── pages/Settings.tsx ─────────────────────────────────────────────────────────
w("pages/Settings.tsx", """
import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { useSettingsStore } from '../stores/settingsStore'
import type { AISettings } from '../types'

const PROVIDERS = [
  { value: 'ollama', label: 'Ollama (local)', defaultUrl: 'http://localhost:11434' },
  { value: 'openai_compat', label: 'OpenAI-compatible', defaultUrl: 'https://api.openai.com/v1' },
  { value: 'openrouter', label: 'OpenRouter', defaultUrl: 'https://openrouter.ai/api/v1' },
  { value: 'lmstudio', label: 'LM Studio / vLLM', defaultUrl: 'http://localhost:1234/v1' },
]

export default function Settings() {
  const { settings, loaded, fetchSettings, saveSettings, testConnection } = useSettingsStore()
  const [form, setForm] = useState<AISettings>(settings)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => { if (!loaded) fetchSettings() }, [])
  useEffect(() => { setForm(settings) }, [settings])

  const set = (key: keyof AISettings, value: string | number) =>
    setForm((f) => ({ ...f, [key]: value }))

  const onProviderChange = (provider: string) => {
    const p = PROVIDERS.find((x) => x.value === provider)
    setForm((f) => ({ ...f, provider, base_url: p?.defaultUrl ?? f.base_url }))
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setStatus(null)
    const res = await saveSettings(form)
    setStatus(res.ok ? { type: 'success', msg: 'Đã lưu settings' } : { type: 'error', msg: res.error ?? 'Lưu thất bại' })
    setSaving(false)
  }

  const handleTest = async () => {
    setTesting(true)
    setStatus(null)
    const res = await testConnection(form)
    setStatus(
      res.ok
        ? { type: 'success', msg: `Kết nối thành công${res.response ? ': ' + res.response : ''}` }
        : { type: 'error', msg: res.error ?? 'Kết nối thất bại' }
    )
    setTesting(false)
  }

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-1 text-xl font-bold text-slate-100">Cài đặt AI</h1>
      <p className="mb-6 text-sm text-slate-500">Cấu hình provider và model để dùng AI writing assistant</p>

      <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-800 bg-slate-900 p-5">
        <div>
          <label className="block text-sm text-slate-400 mb-1">Provider</label>
          <select
            className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-indigo-600 focus:outline-none"
            value={form.provider}
            onChange={(e) => onProviderChange(e.target.value)}
          >
            {PROVIDERS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm text-slate-400 mb-1">Base URL</label>
          <input
            className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
            value={form.base_url}
            onChange={(e) => set('base_url', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm text-slate-400 mb-1">
            API Key <span className="text-slate-600">(lưu local, chưa mã hóa — TODO security)</span>
          </label>
          <input
            type="password"
            className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
            placeholder="Để trống nếu không cần"
            value={form.api_key ?? ''}
            onChange={(e) => set('api_key', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm text-slate-400 mb-1">Model</label>
          <input
            className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none"
            placeholder="e.g. llama3.1:8b, gpt-4o-mini"
            value={form.model}
            onChange={(e) => set('model', e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Temperature</label>
            <input
              type="number" step="0.1" min="0" max="2"
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-indigo-600 focus:outline-none"
              value={form.temperature}
              onChange={(e) => set('temperature', parseFloat(e.target.value))}
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Max tokens</label>
            <input
              type="number" step="256" min="256"
              className="w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-indigo-600 focus:outline-none"
              value={form.max_tokens}
              onChange={(e) => set('max_tokens', parseInt(e.target.value))}
            />
          </div>
        </div>

        {status && (
          <div className={`flex items-center gap-2 rounded-md p-3 text-sm ${
            status.type === 'success' ? 'bg-green-950 text-green-300 border border-green-900' : 'bg-red-950 text-red-300 border border-red-900'
          }`}>
            {status.type === 'success' ? <CheckCircle className="h-4 w-4 flex-shrink-0" /> : <XCircle className="h-4 w-4 flex-shrink-0" />}
            {status.msg}
          </div>
        )}

        <div className="flex gap-3 pt-1">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
            {saving ? 'Đang lưu...' : 'Lưu settings'}
          </button>
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="flex items-center gap-2 rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-slate-600 hover:text-slate-100 disabled:opacity-50"
          >
            {testing && <Loader2 className="h-4 w-4 animate-spin" />}
            {testing ? 'Testing...' : 'Test connection'}
          </button>
        </div>
      </form>
    </div>
  )
}
""")

# ── App.tsx ────────────────────────────────────────────────────────────────────
w("App.tsx", """
import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Chapters from './pages/Chapters'
import Characters from './pages/Characters'
import Lore from './pages/Lore'
import Timeline from './pages/Timeline'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects/:projectId/chapters" element={<Chapters />} />
          <Route path="/projects/:projectId/chapters/:chapterId" element={<Chapters />} />
          <Route path="/projects/:projectId/characters" element={<Characters />} />
          <Route path="/projects/:projectId/lore" element={<Lore />} />
          <Route path="/projects/:projectId/timeline" element={<Timeline />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
""")

# ── main.tsx ───────────────────────────────────────────────────────────────────
w("main.tsx", """
import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import App from './App'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>,
)
""")

print("All frontend files written.")
