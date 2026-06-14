import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Search as SearchIcon, FileText, Globe, Users, Loader2, Bot, X, Send } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api, wsUrl } from '../lib/api'

interface SearchResult {
  id: string
  title: string
  excerpt: string
  kind: 'chapter' | 'lore' | 'character'
  rank: number | null
}

const KIND_CONFIG = {
  chapter:   { icon: FileText,  color: 'text-indigo-400',  border: 'border-indigo-900/50  bg-indigo-950/40'  },
  lore:      { icon: Globe,     color: 'text-emerald-400', border: 'border-emerald-900/50 bg-emerald-950/40' },
  character: { icon: Users,     color: 'text-amber-400',   border: 'border-amber-900/50   bg-amber-950/40'   },
} as const

export default function Search() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // ── Ask AI state ──────────────────────────────────────────────────────────
  const [aiQuestion, setAiQuestion] = useState('')
  const [aiAnswer, setAiAnswer] = useState('')
  const [aiStreaming, setAiStreaming] = useState(false)
  const [showAiPanel, setShowAiPanel] = useState(false)
  const aiWsRef = useRef<WebSocket | null>(null)
  const aiStreamBuf = useRef('')

  // Close WS on unmount
  useEffect(() => () => { aiWsRef.current?.close() }, [])

  const askAi = () => {
    if (!aiQuestion.trim() || !projectId || aiStreaming) return
    setAiStreaming(true)
    setAiAnswer('')
    aiStreamBuf.current = ''

    // Build context from current search results (cap excerpt to avoid token bloat)
    const resultContext = results.slice(0, 10).map(r => {
      const cleanExcerpt = r.excerpt
        ? r.excerpt.replace(/<[^>]+>/g, '').replace(/&[a-z]+;/g, ' ').slice(0, 150)
        : ''
      return `- ${r.kind.toUpperCase()}: ${r.title}${cleanExcerpt ? ` — ${cleanExcerpt}` : ''}`
    }).join('\n')

    const ws = new WebSocket(wsUrl('/ws/ai'))
    aiWsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({
        project_id: projectId,
        action: 'continue',
        text: aiQuestion,
        instruction: results.length > 0
          ? `Dựa trên các kết quả tìm kiếm sau để trả lời:\n${resultContext}`
          : '',
        history: [],
      }))
    }

    ws.onmessage = (e: MessageEvent) => {
      try {
        const msg = JSON.parse(e.data as string) as { delta?: string; done?: boolean; full?: string }
        if (msg.delta) {
          aiStreamBuf.current += msg.delta
          setAiAnswer(aiStreamBuf.current)
        }
        if (msg.done) {
          setAiAnswer(msg.full ?? aiStreamBuf.current)
          setAiStreaming(false)
          aiStreamBuf.current = ''
          ws.close()
        }
      } catch { /* ignore */ }
    }

    ws.onerror = () => setAiStreaming(false)
    ws.onclose = () => setAiStreaming(false)
  }

  const stopAi = () => {
    aiWsRef.current?.close()
    setAiStreaming(false)
  }

  const doSearch = async (q: string) => {
    if (!q.trim() || !projectId) return
    setLoading(true)
    setSearched(true)
    try {
      const data = await api.get<SearchResult[]>(
        `/projects/${projectId}/search?q=${encodeURIComponent(q)}&limit=30`
      )
      setResults(Array.isArray(data) ? data : [])
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    doSearch(query)
  }

  const navigateTo = (r: SearchResult) => {
    if (!projectId) return
    if (r.kind === 'chapter')   navigate(`/projects/${projectId}/chapters/${r.id}`)
    else if (r.kind === 'character') navigate(`/projects/${projectId}/characters`)
    else navigate(`/projects/${projectId}/lore`)
  }

  const grouped = results.reduce<Record<string, SearchResult[]>>((acc, r) => {
    acc[r.kind] = [...(acc[r.kind] ?? []), r]
    return acc
  }, {})

  // Render FTS5 snippets — backend only adds <b> tags, strip everything else
  const safeExcerpt = (html: string) => ({
    __html: html.replace(/<(?!\/?(b)>)[^>]+>/g, ''),
  })

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-1 text-xl font-bold text-slate-100">{t('search.page_title')}</h1>
      <p className="mb-5 text-sm text-slate-500">{t('search.subtitle')}</p>

      <form onSubmit={onSubmit} className="mb-6 flex gap-2">
        <div className="relative flex-1">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            ref={inputRef}
            autoFocus
            className="w-full rounded-lg border border-slate-800 bg-slate-900 py-2.5 pl-9 pr-4 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-700 focus:outline-none"
            placeholder={t('search.placeholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim() || !projectId}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <SearchIcon className="h-4 w-4" />}
          {t('search.button')}
        </button>
      </form>

      {!projectId && (
        <div className="rounded-lg border border-amber-900 bg-amber-950/50 p-3 text-sm text-amber-300">
          {t('search.no_project')}
        </div>
      )}

      {/* Ask AI panel — shown after search or on demand */}
      {projectId && (searched || showAiPanel) && (
        <div className="rounded-lg border border-indigo-900/50 bg-indigo-950/20 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-indigo-400" />
              <span className="text-sm font-medium text-indigo-300">{t('search.ask_ai')}</span>
              {results.length > 0 && (
                <span className="text-[10px] text-indigo-600">
                  {t('search.context_count', { count: results.length })}
                </span>
              )}
            </div>
            {showAiPanel && !searched && (
              <button
                type="button"
                onClick={() => { setShowAiPanel(false); setAiAnswer('') }}
                className="text-slate-600 hover:text-slate-400"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-700 focus:outline-none"
              placeholder={t('search.ai_placeholder')}
              value={aiQuestion}
              onChange={(e) => setAiQuestion(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); askAi() } }}
              disabled={aiStreaming}
            />
            {aiStreaming ? (
              <button
                type="button"
                onClick={stopAi}
                className="flex items-center gap-1.5 rounded-md bg-red-900/80 px-3 py-2 text-sm text-red-200 hover:bg-red-800"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={askAi}
                disabled={!aiQuestion.trim() || aiStreaming}
                className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-40"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          {aiAnswer && (
            <div className="rounded-md border border-slate-800 bg-slate-900 p-3 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto">
              {aiAnswer}
              {aiStreaming && <span className="inline-block h-3.5 w-0.5 bg-indigo-400 animate-pulse ml-0.5" />}
            </div>
          )}
        </div>
      )}

      {/* Show AI panel button when no search done yet */}
      {projectId && !searched && !showAiPanel && (
        <button
          type="button"
          onClick={() => setShowAiPanel(true)}
          className="flex items-center gap-2 text-sm text-slate-600 hover:text-indigo-400 transition-colors"
        >
          <Bot className="h-4 w-4" />
          {t('search.ask_button')}
        </button>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" /> {t('search.loading')}
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="rounded-lg border border-slate-800 p-8 text-center text-sm text-slate-500">
          {t('search.no_results', { query })}
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-6">
          <div className="text-xs text-slate-600">{t('search.results_count', { count: results.length })}</div>
          {(['chapter', 'lore', 'character'] as const).map((kind) => {
            const items = grouped[kind]
            if (!items?.length) return null
            const cfg = KIND_CONFIG[kind]
            const Icon = cfg.icon
            return (
              <section key={kind}>
                <div className="mb-2 flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${cfg.color}`} />
                  <span className={`text-xs font-semibold uppercase tracking-wider ${cfg.color}`}>
                    {t('search.kind_' + kind)} ({items.length})
                  </span>
                </div>
                <div className="space-y-1.5">
                  {items.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => navigateTo(r)}
                      className={`block w-full rounded-lg border p-3 text-left hover:brightness-110 transition-all ${cfg.border}`}
                    >
                      <div className="font-medium text-slate-100">{r.title}</div>
                      {r.excerpt && (
                        <div
                          className="mt-1 line-clamp-2 text-xs text-slate-400 [&_b]:font-semibold [&_b]:text-slate-200"
                          dangerouslySetInnerHTML={safeExcerpt(r.excerpt)}
                        />
                      )}
                    </button>
                  ))}
                </div>
              </section>
            )
          })}
        </div>
      )}
    </div>
  )
}
