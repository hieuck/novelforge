import { useProjectStore } from '../stores/projectStore'

export default function Dashboard() {
  const { projects, fetchProjects, createProject } = useProjectStore()

  const newProject = async () => {
    await createProject({ title: 'Untitled project', status: 'active' })
    await fetchProjects()
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-slate-400">Quản lý project truyện của bạn</p>
        </div>
        <button onClick={newProject} className="rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-100">
          Tạo project mới
        </button>
      </div>
      <div className="grid gap-3">
        {projects.map((p: any) => (
          <a key={p.id} href={`/projects/${p.id}`} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 block">
            <div className="font-medium">{p.title}</div>
            {p.genre && <div className="text-xs text-slate-400">{p.genre}</div>}
            {p.updated_at && (
              <div className="mt-1 text-xs text-slate-500">Cập nhật: {new Date(p.updated_at).toLocaleString()}</div>
            )}
          </a>
        ))}
        {!projects.length && <div className="text-sm text-slate-500">Chưa có project nào.</div>}
      </div>
    </div>
  )
}
