/**
 * Central API client.
 *
 * Dev:        Vite proxy forwards /api → http://127.0.0.1:9000 — use relative URL.
 * Production: preload.js injects window.__NOVELFORGE__.enginePort via contextBridge
 *             so we build http://127.0.0.1:{port}/api/... directly.
 */

declare global {
  interface Window {
    __NOVELFORGE__?: { enginePort: number }
  }
}

function getBase(): string {
  const port = window.__NOVELFORGE__?.enginePort
  return port ? `http://127.0.0.1:${port}/api` : '/api'
}

async function req<T>(path: string, init?: RequestInit, notify = false): Promise<T> {
  const res = await fetch(`${getBase()}${path}`, {
    headers: { 'content-type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const msg = err.detail ?? 'Request failed'
    if (notify) {
      const { useNotificationStore } = await import('../stores/notificationStore')
      useNotificationStore.getState().add('error', msg)
    }
    throw new Error(msg)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get:    <T>(path: string, notify?: boolean)               => req<T>(path, undefined, notify),
  post:   <T>(path: string, body: unknown, notify?: boolean) => req<T>(path, { method: 'POST',  body: JSON.stringify(body) }, notify),
  patch:  <T>(path: string, body: unknown, notify?: boolean) => req<T>(path, { method: 'PATCH', body: JSON.stringify(body) }, notify),
  delete:     (path: string, notify?: boolean)               => req<void>(path, { method: 'DELETE' }, notify),
}

export async function safeReq<T>(label: string, fn: () => Promise<T>): Promise<T | null> {
  try {
    return await fn()
  } catch (e: any) {
    const { useNotificationStore } = await import('../stores/notificationStore')
    useNotificationStore.getState().add('error', `${label}: ${e.message}`)
    return null
  }
}

export type WritingStats = {
  project_id: string
  daily_goal: number
  today_words: number
  total_words: number
  streak: { current: number; longest: number }
  history: { date: string; words_added: number; words_total: number }[]
}

export function wsUrl(path: string): string {
  const port = window.__NOVELFORGE__?.enginePort ?? 9000
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//127.0.0.1:${port}/api${path}`
}
