import { useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { BookOpen } from 'lucide-react'
import { useProjectStore } from './stores/projectStore'
import { api } from './lib/api'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Project from './pages/Project'
import Chapters from './pages/Chapters'
import Characters from './pages/Characters'
import Lore from './pages/Lore'
import Timeline from './pages/Timeline'
import Export from './pages/Export'
import Search from './pages/Search'
import AiPanel from './components/AiPanel'
import AgentPanel from './components/AgentPanel'
import BackgroundJobsPanel from './components/BackgroundJobsPanel'
import Settings from './pages/Settings'

export default function App() {
  const { fetchProjects, projects } = useProjectStore()
  const { hash } = useLocation()
  const projectId = hash.match(/\/projects\/([^/]+)/)?.[1]

  useEffect(() => { fetchProjects() }, [])

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-7xl p-6 space-y-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects/:id" element={<Project />} />
            <Route path="/projects/:id/chapters" element={<Chapters />} />
            <Route path="/projects/:id/characters" element={<Characters />} />
            <Route path="/projects/:id/lore" element={<Lore />} />
            <Route path="/projects/:id/timeline" element={<Timeline />} />
            <Route path="/projects/:id/export" element={<Export />} />
            <Route path="/projects/:id/search" element={<Search />} />
            <Route path="/projects/:id/agent" element={<AgentPanel />} />
            <Route path="/projects/:id/jobs" element={<BackgroundJobsPanel />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<div className="text-sm text-slate-500">Not found</div>} />
          </Routes>
          {projectId && (
            <AiPanel projectId={projectId} />
          )}
        </div>
      </main>
    </div>
  )
}
