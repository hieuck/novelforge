/**
 * Persists agent run history in localStorage per project.
 * Each run stores: task, summary, steps_completed, timestamp.
 */
import { useCallback, useEffect, useState } from 'react'

export interface AgentRun {
  id: string
  task: string
  summary: string
  stepsCompleted: number
  timestamp: string // ISO
}

const MAX_RUNS = 20
const storageKey = (projectId: string) => `novelforge:agent-history:${projectId}`

function load(projectId: string): AgentRun[] {
  try {
    const raw = localStorage.getItem(storageKey(projectId))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function save(projectId: string, runs: AgentRun[]): void {
  try {
    localStorage.setItem(storageKey(projectId), JSON.stringify(runs.slice(0, MAX_RUNS)))
  } catch {
    // localStorage unavailable (private browsing, quota exceeded) — silently ignore
  }
}

export function useAgentHistory(projectId: string | null) {
  const [history, setHistory] = useState<AgentRun[]>(() =>
    projectId ? load(projectId) : [],
  )

  // Re-load when project changes
  useEffect(() => {
    setHistory(projectId ? load(projectId) : [])
  }, [projectId])

  const addRun = useCallback(
    (task: string, summary: string, stepsCompleted: number) => {
      if (!projectId) return
      const run: AgentRun = {
        id: `run-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        task,
        summary,
        stepsCompleted,
        timestamp: new Date().toISOString(),
      }
      setHistory((prev) => {
        const updated = [run, ...prev].slice(0, MAX_RUNS)
        save(projectId, updated)
        return updated
      })
    },
    [projectId],
  )

  const clearHistory = useCallback(() => {
    if (!projectId) return
    localStorage.removeItem(storageKey(projectId))
    setHistory([])
  }, [projectId])

  return { history, addRun, clearHistory }
}
