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
import AgentPanel from './components/AgentPanel'
import ToastContainer from './components/Toast'
import { useAgentSessionStore } from './stores/agentSessionStore'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
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
      <GlobalAgentPanel />
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

function GlobalAgentPanel() {
  const session = useAgentSessionStore((s) => s.session)
  const setPanelOpen = useAgentSessionStore((s) => s.setPanelOpen)
  if (!session.panelOpen) return null
  return (
    <div className="fixed inset-y-0 right-0 z-40">
      <AgentPanel
        projectId={session.projectId}
        chapterId={session.chapterId}
        chapterTitle={session.chapterTitle}
        onInsertText={() => {}}
      />
      <button
        onClick={() => setPanelOpen(false)}
        className="absolute top-2 right-2 rounded p-1 text-slate-500 hover:text-slate-300 z-50"
        title="Close"
      >
        ✕
      </button>
    </div>
  )
}
