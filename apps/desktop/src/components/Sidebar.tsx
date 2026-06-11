import { NavLink } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'

export default function Sidebar() {
  const { projects, fetchProjects } = useProjectStore()

  return (
    <aside className="flex h-full w-60 flex-col border-r border-slate-800/70 bg-slate-900/60">
      <header className="border-b border-slate-800/70 px-4 py-3">
        <div className="text-sm font-semibold text-slate-100">NovelForge</div>
        <div className="text-xs text-slate-500">Offline-first writing</div>
      </header>

      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-3 text-sm">
        <NavLink
          to="/"
          end
          className="block rounded-md px-3 py-2 text-slate-300 hover:bg-slate-800"
        >
          Dashboard
        </NavLink>

        <div className="px-3 pb-1 pt-2 text-[11px] uppercase tracking-wide text-slate-500">
          Projects
        </div>
        {projects.map((p) => (
          <NavLink
            key={p.id}
            to={`/projects/${p.id}/chapters`}
            className="block rounded-md px-3 py-2 text-slate-300 hover:bg-slate-800"
          >
            <div className="truncate">{p.title}</div>
            {p.updated_at && (
              <div className="text-[10px] text-slate-500">
                {new Date(p.updated_at).toLocaleDateString()}
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      <footer className="border-t border-slate-800/70 px-3 py-2 text-[11px] text-slate-500">
        <button onClick={fetchProjects} className="w-full rounded-md border border-slate-800 py-1">
          Refresh
        </button>
      </footer>
    </aside>
  )
}
