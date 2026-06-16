import { lazy, Suspense, useEffect, useState } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Loader2, BookOpen } from 'lucide-react'
import Sidebar from './components/Sidebar'
import { ErrorBoundary } from './components/ErrorBoundary'
import AgentPanel from './components/AgentPanel'
import BackgroundJobsPanel from './components/BackgroundJobsPanel'
import ToastContainer from './components/Toast'
import { useConnectionStore } from './stores/connectionStore'
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

function SplashScreen() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 bg-slate-950">
      <BookOpen className="h-12 w-12 text-indigo-400" />
      <div className="text-xl font-bold text-slate-100">NovelForge</div>
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        Connecting to engine...
      </div>
    </div>
  )
}

export default function App() {
  const loc = useLocation()
  const pidMatch = loc.pathname.match(/^\/projects\/([^/]+)/)
  const urlProjectId = pidMatch?.[1] ?? null
  const { session, start } = useAgentSessionStore()
  const { connected, checking, check } = useConnectionStore()
  const [initialCheckDone, setInitialCheckDone] = useState(false)
  const isRunning = session.status === 'planning' || session.status === 'running' || session.status === 'asking'

  useEffect(() => {
    check().finally(() => setInitialCheckDone(true))
    const t = setInterval(check, 15000)
    return () => clearInterval(t)
  }, [check])

  useEffect(() => {
    if (urlProjectId && !session.projectId) {
      start(urlProjectId)
    }
  }, [urlProjectId])

  if (!initialCheckDone || (checking && !connected)) {
    return <SplashScreen />
  }

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
      {/* Connection status bar */}
      {!connected && (
        <div className="flex items-center gap-2 border-t border-slate-800 bg-red-950/40 px-4 py-1.5 text-xs text-red-400">
          <span className="inline-block h-2 w-2 rounded-full bg-red-500" />
          Engine disconnected — retrying...
        </div>
      )}
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

function AgentJobsPage() {
  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex-1 overflow-hidden">
        <BackgroundJobsPanel />
      </div>
    </div>
  )
}
