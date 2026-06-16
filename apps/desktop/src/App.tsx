import { lazy, Suspense, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import Sidebar from './components/Sidebar'
import { ErrorBoundary } from './components/ErrorBoundary'
import AgentPanel from './components/AgentPanel'
import BackgroundJobsPanel from './components/BackgroundJobsPanel'
import ToastContainer from './components/Toast'
import { useAgentSessionStore } from './stores/agentSessionStore'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const ChapterPage = lazy(() => import('./pages/Chapters'))
const Characters = lazy(() => import('./pages/Characters'))
const Lore = lazy(() => import('./pages/Lore'))
const Timeline = lazy(() => import('./pages/Timeline'))
const Settings = lazy(() => import('./pages/Settings'))
const Export = lazy(() => import('./pages/Export'))
const Search = lazy(() => import('./pages/Search'))
const Gallery = lazy(() => import('./pages/Gallery'))
const Storyboard = lazy(() => import('./pages/Storyboard'))
const ProjectPage = lazy(() => import('./pages/Project'))

function PageFallback() {
  return (
    <div className="flex h-full items-center justify-center text-slate-500">
      <Loader2 className="h-5 w-5 animate-spin" />
    </div>
  )
}

function Lazy({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageFallback />}><ErrorBoundary>{children}</ErrorBoundary></Suspense>
}

export default function App() {
  const loc = useLocation()
  const pidMatch = loc.pathname.match(/^\/projects\/([^/]+)/)
  const urlProjectId = pidMatch?.[1] ?? null
  const { session, start } = useAgentSessionStore()
  const isRunning = session.status === 'planning' || session.status === 'running' || session.status === 'asking'

  useEffect(() => {
    if (urlProjectId && !session.projectId) {
      start(urlProjectId)
    }
  }, [urlProjectId])

  const showRight = urlProjectId || (session.projectId && session.status !== 'idle')

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-950 text-slate-100">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Lazy><Dashboard /></Lazy>} />
            <Route path="/projects/:projectId" element={<Lazy><ProjectPage /></Lazy>} />
            <Route path="/projects/:projectId/chapters" element={<Lazy><ChapterPage /></Lazy>} />
            <Route path="/projects/:projectId/chapters/:chapterId" element={<Lazy><ChapterPage /></Lazy>} />
            <Route path="/projects/:projectId/characters" element={<Lazy><Characters /></Lazy>} />
            <Route path="/projects/:projectId/lore" element={<Lazy><Lore /></Lazy>} />
            <Route path="/projects/:projectId/timeline" element={<Lazy><Timeline /></Lazy>} />
            <Route path="/projects/:projectId/export" element={<Lazy><Export /></Lazy>} />
            <Route path="/projects/:projectId/search" element={<Lazy><Search /></Lazy>} />
            <Route path="/projects/:projectId/gallery" element={<Lazy><Gallery /></Lazy>} />
            <Route path="/projects/:projectId/storyboard" element={<Lazy><Storyboard /></Lazy>} />
            <Route path="/projects/:projectId/agent-jobs" element={<Lazy><AgentJobsPage /></Lazy>} />
            <Route path="/settings" element={<Lazy><Settings /></Lazy>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        {showRight && (
          <div className="w-80 border-l border-slate-800 flex-shrink-0">
            <AgentPanel
              projectId={urlProjectId || session.projectId}
              chapterId={null}
              chapterTitle={null}
              onInsertText={() => {}}
            />
          </div>
        )}
      </div>
      {/* Bottom status bar */}
      {isRunning && (
        <div className="flex items-center gap-2 border-t border-slate-800 bg-slate-900 px-4 py-1.5 text-xs text-slate-400">
          <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          AI Agent đang chạy
          <span className="ml-auto text-slate-600">{session.status === 'planning' ? 'Planning...' : 'Đang thực thi...'}</span>
        </div>
      )}
      <ToastContainer />
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
