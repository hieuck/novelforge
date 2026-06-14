import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import { ErrorBoundary } from './components/ErrorBoundary'
import AgentPanel from './components/AgentPanel'
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
      <GlobalAgentFloating />
    </div>
  )
}

function GlobalAgentFloating() {
  const loc = useLocation()
  const pidMatch = loc.pathname.match(/^\/projects\/([^/]+)/)
  const urlProjectId = pidMatch?.[1] ?? null
  const { session, start, setPanelOpen } = useAgentSessionStore()

  useEffect(() => {
    if (urlProjectId) {
      if (!session.projectId) {
        start(urlProjectId)
      }
    }
  }, [urlProjectId])

  const hasSession = session.projectId !== null && session.projectId !== undefined
  const activePid = urlProjectId || session.projectId

  // Only show button when on a project page; keep panel mounted if session exists
  return (
    <>
      {urlProjectId && (
        <button
          onClick={() => setPanelOpen(!session.panelOpen)}
          className={`fixed right-0 top-1/2 z-30 -translate-y-1/2 rounded-l-lg border border-r-0 border-slate-700 p-2 text-xs transition-colors ${
            session.panelOpen
              ? 'bg-indigo-900/70 text-indigo-300 border-indigo-700'
              : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
          }`}
          title="AI Agent"
        >
          🤖
          {session.status !== 'idle' && (
            <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          )}
        </button>
      )}

      {/* Panel — always mounted once started, CSS hide/show to preserve WebSocket */}
      {hasSession && (
        <div className={`fixed right-0 top-0 z-20 h-full border-l border-slate-800 bg-slate-950 shadow-2xl transition-all duration-300 ${session.panelOpen ? 'translate-x-0' : 'translate-x-full'}`}>
          <AgentPanel
            projectId={activePid}
            chapterId={null}
            chapterTitle={null}
            onInsertText={() => {}}
          />
        </div>
      )}
    </>
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
