import { lazy, Suspense, useEffect, useState, useMemo } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Loader2, BookOpen } from 'lucide-react'
import Sidebar from './components/Sidebar'
import { ErrorBoundary } from './components/ErrorBoundary'
import AgentPanel from './components/AgentPanel'
import BackgroundJobsPanel from './components/BackgroundJobsPanel'
import ToastContainer from './components/Toast'
import { useConnectionStore } from './stores/connectionStore'
import { useProjectStore } from './stores/projectStore'
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
  const { projects } = useProjectStore()
  const [initialCheckDone, setInitialCheckDone] = useState(false)
  const isRunning = session.status === 'planning' || session.status === 'running' || session.status === 'asking'

  const currentProject = useMemo(() => projects.find((p) => p.id === urlProjectId), [projects, urlProjectId])

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
      {/* Status bar */}
      <div className="flex items-center gap-3 border-t border-slate-800 bg-slate-900/80 px-4 py-1.5 text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <span className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
        {currentProject?.word_count !== undefined && currentProject.word_count > 0 && (
          <span className="text-indigo-400/70">{currentProject.word_count.toLocaleString()} words</span>
        )}
        {isRunning && (
          <span className="flex items-center gap-1.5 text-green-400/70">
            <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            AI Agent {session.status === 'planning' ? 'planning...' : 'running...'}
          </span>
        )}
      </div>
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
