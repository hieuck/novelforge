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
  const isRunning = session.status === 'planning' || session.status === 'running' || session.status === 'asking'

  return (
    <div className={`fixed inset-y-0 right-0 z-40 transition-transform ${session.panelOpen ? 'translate-x-0' : 'translate-x-full'}`}>
      <div className="relative h-full">
        <AgentPanel
          projectId={session.projectId}
          chapterId={session.chapterId}
          chapterTitle={session.chapterTitle}
          onInsertText={() => {}}
        />
        {/* Minimize button */}
        <button
          onClick={() => setPanelOpen(false)}
          className="absolute top-2 right-2 rounded p-1 text-slate-500 hover:text-slate-300 z-50"
          title="Close"
        >
          ✕
        </button>
      </div>
      {/* When minimized but agent running: show a thin status bar */}
      {!session.panelOpen && isRunning && (
        <button
          onClick={() => setPanelOpen(true)}
          className="fixed bottom-0 left-0 right-0 z-50 flex items-center gap-2 border-t border-green-800/60 bg-slate-900 px-4 py-2 text-sm text-green-400 shadow-lg"
        >
          <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          AI Agent đang chạy...
        </button>
      )}
    </div>
  )
}
