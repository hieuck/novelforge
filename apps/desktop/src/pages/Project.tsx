import { useParams } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'

export default function Project() {
  const { projectId } = useParams()
  const projects = useProjectStore((state) => state.projects)
  const { fetchProjects, createProject } = useProjectStore()
  const project = projects.find((p: any) => p.id === projectId) || projects[0]

  return (
    <div className="flex h-full">
      <div className="w-64 border-r border-slate-800/70 bg-slate-900/60 p-3 text-sm">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">Project</span>
          <button
            className="rounded bg-slate-800 px-2 py-1 text-xs"
            onClick={async () => {
              const title = prompt('Project title')
              if (!title || !projectId) return
              await createProject({ title, status: 'active' })
              await fetchProjects()
            }}
          >
            New project
          </button>
        </div>
        <div className="space-y-1">
          {projects.map((p: any) => (
            <div key={p.id} className={`rounded-md px-3 py-2 ${p.id === projectId ? 'bg-slate-800 text-slate-100' : 'text-slate-400'}`}>
              <div className="truncate">{p.title}</div>
              {p.updated_at && <div className="text-[10px] text-slate-500">{new Date(p.updated_at).toLocaleDateString()}</div>}
            </div>
          ))}
          {!projects.length && <div className="text-xs text-slate-500">No projects. Create one.</div>}
        </div>
      </div>
      <main className="flex-1 p-6 text-slate-500">{project ? `Project: ${project.title}` : 'Select or create a project.'}</main>
    </div>
  )
}
