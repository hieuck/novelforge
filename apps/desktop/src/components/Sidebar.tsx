import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { BookOpen, Settings, LayoutDashboard, Users, Globe, Clock, FileText, Download, Search, SlidersHorizontal, Sparkles, Image as ImageIcon, Film } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useProjectStore } from '../stores/projectStore'
import { useConnectionStore } from '../stores/connectionStore'
import { api } from '../lib/api'

export default function Sidebar() {
  const { t } = useTranslation()
  const { projects, fetchProjects } = useProjectStore()
  const { connected, check } = useConnectionStore()
  const location = useLocation()
  // With HashRouter, location.pathname gives us the path after #
  const projectId = location.pathname.match(/^\/projects\/([^/]+)/)?.[1] ?? null
  const [activeJobs, setActiveJobs] = useState(0)

  useEffect(() => { fetchProjects() }, [fetchProjects])

  // Poll active job count for the current project
  useEffect(() => {
    if (!projectId) { setActiveJobs(0); return }
    let cancelled = false
    const check = async () => {
      try {
        const jobs = await api.get<Array<{ status: string; kind: string }>>(`/projects/${projectId}/jobs?limit=20`)
        if (!cancelled) {
          setActiveJobs(jobs.filter((j) => j.kind === 'agent' && (j.status === 'queued' || j.status === 'running')).length)
        }
      } catch { /* ignore */ }
    }
    check()
    const t = setInterval(check, 5000)
    return () => { cancelled = true; clearInterval(t) }
  }, [projectId])

  // Poll engine health every 15s
  useEffect(() => {
    check()
    const t = setInterval(check, 15000)
    return () => clearInterval(t)
  }, [check])

  const navCls = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
      isActive ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
    }`

  return (
    <aside className="flex h-full w-56 flex-col border-r border-slate-800 bg-slate-950">
      <header className="border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-bold text-slate-100">{t('app.name')}</span>
        </div>
        <div className="mt-0.5 text-[11px] text-slate-500">{t('app.tagline')}</div>
      </header>

      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        <NavLink to="/" end className={navCls} title="Dashboard">
          <LayoutDashboard className="h-4 w-4" />
          {t('nav.dashboard')}
        </NavLink>

        {projectId && (
          <>
            <div className="mt-3 px-3 pb-1 text-[10px] uppercase tracking-wider text-slate-600">{t('nav.project')}</div>
            <NavLink to={`/projects/${projectId}`} end className={navCls} title="Project settings">
              <SlidersHorizontal className="h-4 w-4" />{t('nav.project_info')}
            </NavLink>
            <NavLink to={`/projects/${projectId}/chapters`} className={navCls} title="Edit chapters">
              <FileText className="h-4 w-4" />{t('nav.chapters')}
            </NavLink>
            <NavLink to={`/projects/${projectId}/characters`} className={navCls} title="Manage characters">
              <Users className="h-4 w-4" />{t('nav.characters')}
            </NavLink>
            <NavLink to={`/projects/${projectId}/lore`} className={navCls} title="World-building lore">
              <Globe className="h-4 w-4" />{t('nav.lore')}
            </NavLink>
            <NavLink to={`/projects/${projectId}/timeline`} className={navCls} title="Timeline events">
              <Clock className="h-4 w-4" />{t('nav.timeline')}
            </NavLink>
            <NavLink to={`/projects/${projectId}/export`} className={navCls} title="Export story">
              <Download className="h-4 w-4" />{t('nav.export')}
            </NavLink>
            <NavLink to={`/projects/${projectId}/search`} className={navCls} title="Search">
              <Search className="h-4 w-4" />{t('nav.search')}
            </NavLink>
            <NavLink to={`/projects/${projectId}/gallery`} className={navCls} title="Image gallery">
              <ImageIcon className="h-4 w-4" />Gallery
            </NavLink>
            <NavLink to={`/projects/${projectId}/storyboard`} className={navCls} title="Storyboard & video">
              <Film className="h-4 w-4" />Storyboard
            </NavLink>
            <NavLink to={`/projects/${projectId}/agent-jobs`} className={navCls} title="Background agent jobs">
              <Sparkles className="h-4 w-4" />
              <span>{t('nav.agent_jobs')}</span>
              {activeJobs > 0 && (
                <span className="ml-auto rounded-full bg-yellow-900/60 px-1.5 py-0.5 text-[10px] text-yellow-300">
                  {activeJobs}
                </span>
              )}
            </NavLink>
          </>
        )}

        {projects.length > 0 && (
          <>
            <div className="mt-3 px-3 pb-1 text-[10px] uppercase tracking-wider text-slate-600">{t('nav.projects')}</div>
            {projects.slice(0, 10).map((p) => (
              <NavLink key={p.id} to={`/projects/${p.id}/chapters`}
                className={({ isActive }) =>
                  `block rounded-md px-3 py-2 text-sm transition-colors ${
                    isActive || p.id === projectId ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`
                }>
                <div className="truncate font-medium">{p.title}</div>
                {p.genre && <div className="text-[10px] text-slate-500">{p.genre}</div>}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <footer className="border-t border-slate-800 px-2 py-2">
        <NavLink to="/settings" className={navCls} title="Application settings">
          <Settings className="h-4 w-4" />{t('nav.settings')}
        </NavLink>
        <div className="mt-1 flex items-center gap-2 px-3 py-1.5 text-xs text-slate-500">
          <span className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          {t('nav.ai_engine')}
        </div>
      </footer>
    </aside>
  )
}
