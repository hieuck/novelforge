import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Project from './pages/Project'
import Chapters from './pages/Chapters'
import Characters from './pages/Characters'
import Lore from './pages/Lore'
import Timeline from './pages/Timeline'
import Settings from './pages/Settings'

export default function App() {
  return (
    <HashRouter>
      <div className="flex h-screen bg-slate-950 text-slate-100">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<Dashboard />} />
            <Route path="/projects/:projectId" element={<Project />} />
            <Route path="/projects/:projectId/chapters" element={<Chapters />} />
            <Route path="/projects/:projectId/chapters/:chapterId" element={<Chapters />} />
            <Route path="/projects/:projectId/characters" element={<Characters />} />
            <Route path="/projects/:projectId/lore" element={<Lore />} />
            <Route path="/projects/:projectId/timeline" element={<Timeline />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  )
}
