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
import ToastContainer from './components/Toast'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<ErrorBoundary><Dashboard /></ErrorBoundary>} />
          <Route path="/projects/:projectId" element={<ErrorBoundary><ProjectPage /></ErrorBoundary>} />
          <Route path="/projects/:projectId/chapters" element={<ErrorBoundary><Chapters /></ErrorBoundary>} />
          <Route path="/projects/:projectId/chapters/:chapterId" element={<ErrorBoundary><Chapters /></ErrorBoundary>} />
          <Route path="/projects/:projectId/characters" element={<ErrorBoundary><Characters /></ErrorBoundary>} />
          <Route path="/projects/:projectId/lore" element={<ErrorBoundary><Lore /></ErrorBoundary>} />
          <Route path="/projects/:projectId/timeline" element={<ErrorBoundary><Timeline /></ErrorBoundary>} />
          <Route path="/projects/:projectId/export" element={<ErrorBoundary><Export /></ErrorBoundary>} />
          <Route path="/projects/:projectId/search" element={<ErrorBoundary><Search /></ErrorBoundary>} />
          <Route path="/projects/:projectId/agent-jobs" element={<ErrorBoundary><AgentJobsPage /></ErrorBoundary>} />
          <Route path="/settings" element={<ErrorBoundary><Settings /></ErrorBoundary>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <ToastContainer />
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
