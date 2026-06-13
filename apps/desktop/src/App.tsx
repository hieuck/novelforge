import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import { ErrorBoundary } from './components/ErrorBoundary'
import Dashboard from './pages/Dashboard'
import Chapters from './pages/Chapters'
import Characters from './pages/Characters'
import Lore from './pages/Lore'
import Timeline from './pages/Timeline'
import Settings from './pages/Settings'
import Export from './pages/Export'
import Search from './pages/Search'
import ProjectPage from './pages/Project'
import BackgroundJobsPanel from './components/BackgroundJobsPanel'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects/:projectId" element={<ProjectPage />} />
            <Route path="/projects/:projectId/chapters" element={<Chapters />} />
            <Route path="/projects/:projectId/chapters/:chapterId" element={<Chapters />} />
            <Route path="/projects/:projectId/characters" element={<Characters />} />
            <Route path="/projects/:projectId/lore" element={<Lore />} />
            <Route path="/projects/:projectId/timeline" element={<Timeline />} />
            <Route path="/projects/:projectId/export" element={<Export />} />
            <Route path="/projects/:projectId/search" element={<Search />} />
            <Route path="/projects/:projectId/agent-jobs" element={<AgentJobsPage />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  )
}

function AgentJobsPage() {
  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex-1 overflow-hidden">
        <BackgroundJobsPanel />
      </div>
    </div>
  )
}
