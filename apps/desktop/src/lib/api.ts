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

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${getBase()}${path}`, {
    headers: { 'content-type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Request failed')
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get:    <T>(path: string)               => req<T>(path),
  post:   <T>(path: string, body: unknown) => req<T>(path, { method: 'POST',  body: JSON.stringify(body) }),
  patch:  <T>(path: string, body: unknown) => req<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete:     (path: string)               => req<void>(path, { method: 'DELETE' }),
}

export function wsUrl(path: string): string {
  const port = window.__NOVELFORGE__?.enginePort ?? 9000
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//127.0.0.1:${port}/api${path}`
}
