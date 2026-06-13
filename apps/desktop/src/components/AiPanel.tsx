import { useRef, useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  Send, Trash2, Bot, Zap, Square, ClipboardCopy,
  Brain, ChevronDown, ChevronUp, Copy, Check, Search,
} from 'lucide-react'
import { useAiStore } from '../stores/aiStore'
import { useChapterStore } from '../stores/chapterStore'
import { AI_ACTIONS, type AIAction } from '../types'
import { wsUrl } from '../lib/api'

// ── Group actions for grouped selector ───────────────────────────────────────

const ACTION_GROUPS = Array.from(
  AI_ACTIONS.reduce((map, a) => {
    const list = map.get(a.group) ?? []
    list.push(a)
    map.set(a.group, list)
    return map
  }, new Map<string, typeof AI_ACTIONS[number][]>()),
)

// ── Context badge ─────────────────────────────────────────────────────────────

function ContextBadge({ hasChapter, hasProject }: { hasChapter: boolean; hasProject: boolean }) {
  if (!hasChapter && !hasProject) return null
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-slate-800 bg-slate-900/60">
      <Brain className="h-3 w-3 text-indigo-400 shrink-0" />
      <span className="text-[10px] text-slate-500">
        Context:{' '}
        {[hasProject && 'project', hasChapter && 'chapter']
          .filter(Boolean)
          .join(' + ')}
      </span>
    </div>
  )
}

// ── Action selector with search ───────────────────────────────────────────────

function ActionSelector({
  value,
  onChange,
}: {
  value: AIAction
  onChange: (v: AIAction) => void
}) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  const selected = AI_ACTIONS.find((a) => a.value === value)

  const filtered = query.trim()
    ? AI_ACTIONS.filter(
        (a) =>
          a.label.toLowerCase().includes(query.toLowerCase()) ||
          a.value.includes(query.toLowerCase()),
      )
    : null

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const select = (v: AIAction) => {
    onChange(v)
    setOpen(false)
    setQuery('')
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-md border border-slate-800 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-300 hover:border-slate-700 focus:outline-none"
      >
        <span>{selected?.label ?? 'Chọn action'}</span>
        <ChevronDown className="h-3 w-3 text-slate-500 shrink-0" />
      </button>

      {open && (
        <div className="absolute bottom-full left-0 right-0 z-50 mb-1 rounded-md border border-slate-700 bg-slate-900 shadow-xl">
          {/* Search */}
          <div className="flex items-center gap-2 border-b border-slate-800 px-2.5 py-2">
            <Search className="h-3 w-3 text-slate-500 shrink-0" />
            <input
              autoFocus
              className="w-full bg-transparent text-xs text-slate-300 placeholder:text-slate-600 focus:outline-none"
              placeholder="Tìm action…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="max-h-56 overflow-y-auto py-1">
            {filtered ? (
              filtered.length > 0 ? (
                filtered.map((a) => (
                  <ActionItem key={a.value} action={a} current={value} onSelect={select} />
                ))
              ) : (
                <p className="px-3 py-2 text-[11px] text-slate-600">Không tìm thấy</p>
              )
            ) : (
              ACTION_GROUPS.map(([group, actions]) => (
                <div key={group}>
                  <p className="px-3 pt-2 pb-0.5 text-[9px] font-semibold uppercase tracking-wider text-slate-600">
                    {group}
                  </p>
                  {actions.map((a) => (
                    <ActionItem key={a.value} action={a} current={value} onSelect={select} />
                  ))}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function ActionItem({
  action,
  current,
  onSelect,
}: {
  action: typeof AI_ACTIONS[number]
  current: AIAction
  onSelect: (v: AIAction) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(action.value)}
      className={`w-full px-3 py-1.5 text-left text-xs transition-colors ${
        action.value === current
          ? 'bg-indigo-900/50 text-indigo-300'
          : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
      }`}
    >
      {action.label}
    </button>
  )
}

// ── Copy button ───────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopied(true)
        setTimeout(() => setCopied(false), 1500)
      })
      .catch(() => {
        // clipboard unavailable in non-secure context — silently ignore
      })
  }
  return (
    <button
      type="button"
      onClick={copy}
      title="Copy"
      className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors"
    >
      {copied ? <Check className="h-3 w-3 text-green-400" /> : <Copy className="h-3 w-3" />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

// ── Message bubble ────────────────────────────────────────────────────────────

function MessageBubble({
  role,
  content,
  onInsert,
}: {
  role: 'user' | 'assistant'
  content: string
  onInsert?: (text: string) => void
}) {
  const [expanded, setExpanded] = useState(true)
  const isLong = content.length > 600
  const displayContent = expanded ? content : content.slice(0, 600) + '…'

  return (
    <div
      className={`rounded-lg p-3 text-sm ${
        role === 'user'
          ? 'bg-slate-800 text-slate-100'
          : 'border border-slate-800 bg-slate-900 text-slate-200'
      }`}
    >
      <div className="mb-1.5 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-wide text-slate-500">
          {role === 'user' ? 'Bạn' : 'AI Assistant'}
        </span>
        {role === 'assistant' && (
          <div className="flex items-center gap-1">
            <CopyButton text={content} />
            {onInsert && (
              <button
                type="button"
                onClick={() => onInsert(content)}
                title="Chèn vào editor"
                className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors"
              >
                <ClipboardCopy className="h-3 w-3" />
                Chèn
              </button>
            )}
          </div>
        )}
      </div>
      <div className="whitespace-pre-wrap leading-relaxed">{displayContent}</div>
      {isLong && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mt-1.5 flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-400"
        >
          {expanded
            ? <><ChevronUp className="h-3 w-3" /> Thu gọn</>
            : <><ChevronDown className="h-3 w-3" /> Xem thêm</>}
        </button>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

interface AiPanelProps {
  projectId?: string | null
  chapterId?: string | null
  /** Called when user clicks "Insert" on an AI response — passes text to the editor */
  onInsertText?: (text: string) => void
}

export default function AiPanel({
  projectId: propProjectId,
  chapterId: propChapterId,
  onInsertText,
}: AiPanelProps) {
  const params = useParams()
  const projectId = propProjectId ?? params.projectId ?? null
  const { messages, loading, clearMessages, addUserMessage, addAssistantMessage, getHistory } =
    useAiStore()
  const { activeChapterId: storeChapterId } = useChapterStore()
  const activeChapterId = propChapterId ?? storeChapterId

  const [input, setInput] = useState('')
  const [instruction, setInstruction] = useState('')
  const [showInstruction, setShowInstruction] = useState(false)
  const [action, setAction] = useState<AIAction>('continue')
  const [streamText, setStreamText] = useState('')
  const [streaming, setStreaming] = useState(false)

  const bottomRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const streamBuf = useRef('')

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamText])

  useEffect(() => () => { wsRef.current?.close() }, [])

  const sendStreaming = useCallback(
    (text: string) => {
      if (!text.trim()) return

      // Snapshot history BEFORE adding the new user message
      const history = getHistory()

      setStreaming(true)
      setStreamText('')
      streamBuf.current = ''
      addUserMessage(text)

      const ws = new WebSocket(wsUrl('/ws/ai'))
      wsRef.current = ws

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            project_id: projectId ?? null,
            chapter_id: activeChapterId ?? null,
            action,
            text,
            instruction: instruction.trim(),
            history,
          }),
        )
      }

      ws.onmessage = (e: MessageEvent) => {
        try {
          const msg = JSON.parse(e.data as string) as {
            delta?: string
            done?: boolean
            full?: string
            error?: string
          }
          if (msg.error) {
            addAssistantMessage(`Lỗi: ${msg.error}`)
            setStreamText('')
            streamBuf.current = ''
            setStreaming(false)
            ws.close()
            return
          }
          if (msg.delta) {
            streamBuf.current += msg.delta
            setStreamText(streamBuf.current)
          }
          if (msg.done) {
            addAssistantMessage(msg.full ?? streamBuf.current)
            setStreamText('')
            streamBuf.current = ''
            setStreaming(false)
            ws.close()
          }
        } catch {
          // ignore malformed frames
        }
      }

      ws.onerror = () => {
        // Fallback to HTTP if WS unavailable
        const store = useAiStore.getState()
        store.sendMessage(text, { projectId, chapterId: activeChapterId, action })
        setStreamText('')
        streamBuf.current = ''
        setStreaming(false)
      }

      ws.onclose = () => setStreaming(false)
    },
    [projectId, activeChapterId, action, instruction, addUserMessage, addAssistantMessage, getHistory],
  )

  const stopStream = () => {
    wsRef.current?.close()
    if (streamBuf.current) addAssistantMessage(streamBuf.current + ' [stopped]')
    setStreamText('')
    streamBuf.current = ''
    setStreaming(false)
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading || streaming) return
    setInput('')
    sendStreaming(text)
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      submit(e as unknown as React.FormEvent)
    }
  }

  const isActive = loading || streaming
  const turnCount = Math.floor(messages.length / 2)

  return (
    <aside className="flex h-full w-80 flex-col bg-slate-950">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-semibold text-slate-200">AI Agent</span>
          {streaming && <Zap className="h-3.5 w-3.5 animate-pulse text-yellow-400" />}
          {turnCount > 0 && (
            <span className="rounded-full bg-indigo-900/60 px-1.5 py-0.5 text-[10px] text-indigo-300">
              {turnCount} turns
            </span>
          )}
        </div>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={clearMessages}
            title="Xóa hội thoại"
            className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
      </header>

      {/* Context indicator */}
      <ContextBadge hasChapter={!!activeChapterId} hasProject={!!projectId} />

      {/* Message list */}
      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        {messages.length === 0 && !streamText && (
          <div className="mt-6 space-y-2 text-center">
            <Bot className="mx-auto h-8 w-8 text-slate-700" />
            <p className="text-xs text-slate-600">
              Chọn action, nhập yêu cầu, nhấn Ctrl+Enter
            </p>
            <p className="text-[10px] text-slate-700">
              Hội thoại nhiều lượt — AI nhớ ngữ cảnh cuộc trò chuyện
            </p>
          </div>
        )}

        {messages.map((m) => (
          <MessageBubble
            key={m.id}
            role={m.role}
            content={m.content}
            onInsert={m.role === 'assistant' ? onInsertText : undefined}
          />
        ))}

        {/* Streaming bubble */}
        {streamText && (
          <div className="rounded-lg border border-indigo-900/40 bg-slate-900 p-3 text-sm">
            <div className="mb-1.5 flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-indigo-400">
              <Zap className="h-3 w-3" />
              AI Agent (đang viết…)
            </div>
            <div className="whitespace-pre-wrap leading-relaxed text-slate-200">
              {streamText}
            </div>
            <div className="mt-1.5 flex gap-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="inline-block h-1 w-1 rounded-full bg-indigo-400 animate-bounce"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
          </div>
        )}

        {loading && !streaming && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <div className="mb-1 text-[10px] text-slate-500">AI Agent</div>
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="inline-block h-1.5 w-1.5 rounded-full bg-indigo-400 animate-bounce"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input form */}
      <form onSubmit={submit} className="space-y-2 border-t border-slate-800 p-3">
        {/* Action selector */}
        <ActionSelector value={action} onChange={setAction} />

        {/* Optional instruction */}
        <div>
          <button
            type="button"
            onClick={() => setShowInstruction((v) => !v)}
            className="flex items-center gap-1 text-[10px] text-slate-600 hover:text-slate-400 transition-colors"
          >
            {showInstruction
              ? <><ChevronUp className="h-3 w-3" /> Ẩn hướng dẫn thêm</>
              : <><ChevronDown className="h-3 w-3" /> Thêm hướng dẫn cụ thể…</>}
          </button>
          {showInstruction && (
            <textarea
              className="mt-1.5 h-14 w-full resize-none rounded-md border border-slate-800 bg-slate-900 p-2 text-xs text-slate-300 placeholder:text-slate-600 focus:border-indigo-700 focus:outline-none"
              placeholder="VD: Giữ ngôn ngữ trang trọng, tránh từ Hán-Việt…"
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
            />
          )}
        </div>

        {/* Main input */}
        <textarea
          className="h-20 w-full resize-none rounded-md border border-slate-800 bg-slate-900 p-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-700 focus:outline-none disabled:opacity-50"
          placeholder="Nhập yêu cầu hoặc paste đoạn văn… (Ctrl+Enter)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={isActive}
        />

        {streaming ? (
          <button
            type="button"
            onClick={stopStream}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-red-900/80 px-3 py-2 text-sm font-medium text-red-200 hover:bg-red-800"
          >
            <Square className="h-3.5 w-3.5" />
            Dừng
          </button>
        ) : (
          <button
            type="submit"
            disabled={isActive || !input.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
          >
            <Send className="h-3.5 w-3.5" />
            {loading ? 'Đang xử lý…' : 'Gửi'}
          </button>
        )}
      </form>
    </aside>
  )
}
