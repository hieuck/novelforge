import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Bot, Play, Square, Trash2, CheckCircle, Loader2, Zap,
  AlertCircle, User, Globe, FileText, Sparkles, Calendar,
  ChevronDown, ChevronUp, Copy, Check, ClipboardCopy,
  HelpCircle, RefreshCw, Search, History, X,
} from 'lucide-react'
import { wsUrl } from '../lib/api'
import { useAgentHistory, type AgentRun } from '../hooks/useAgentHistory'

// ── Types ────────────────────────────────────────────────────────────────────

type AgentStatus = 'idle' | 'planning' | 'running' | 'asking' | 'done' | 'cancelled' | 'error'

interface PlanStep {
  step: number
  tool: string
  description: string
}

interface ToolOutput {
  step: number
  tool: string
  description: string
  result: Record<string, any>
}

// ── Preset tasks ──────────────────────────────────────────────────────────────

function getPresets(chapterTitle?: string | null) {
  return [
    { label: '3 nhân vật', task: 'Tạo 3 nhân vật cho truyện fantasy: anh hùng, phản diện, và người thầy. Mỗi nhân vật cần tính cách, mục tiêu và bí mật riêng.' },
    { label: 'Chương mở đầu', task: 'Viết chương mở đầu hấp dẫn, giới thiệu thế giới và nhân vật chính. Khoảng 500 từ.' },
    { label: 'Mở rộng lore', task: 'Đọc các nhân vật hiện có rồi tạo 3 lore items phù hợp: 1 địa điểm, 1 tổ chức, 1 yếu tố magic.' },
    { label: 'Tóm tắt project', task: 'Đọc toàn bộ thông tin project rồi viết tóm tắt cốt truyện súc tích, cập nhật vào project summary.' },
    { label: 'Timeline sự kiện', task: 'Đọc các chương hiện có và tạo 3-5 timeline events quan trọng theo thứ tự thời gian.' },
    { label: 'Kiểm tra nhất quán', task: 'Kiểm tra toàn bộ project để tìm mâu thuẫn về nhân vật, timeline và cốt truyện. Liệt kê mọi vấn đề tìm thấy.' },
    ...(chapterTitle
      ? [{ label: 'Cải thiện chương này', task: `Đọc chương "${chapterTitle}", viết lại để tăng chất lượng văn phong, nhịp độ và cảm xúc. Lưu lại chương sau khi hoàn thành.` }]
      : []),
  ]
}

// ── Tool metadata ─────────────────────────────────────────────────────────────

const TOOL_META: Record<string, { color: string; bg: string; border: string; icon: React.ReactNode }> = {
  create_character: {
    color: 'text-amber-400', bg: 'bg-amber-950/40', border: 'border-amber-800/50',
    icon: <User className="h-3.5 w-3.5 text-amber-400" />,
  },
  update_character: {
    color: 'text-amber-300', bg: 'bg-amber-950/30', border: 'border-amber-700/40',
    icon: <User className="h-3.5 w-3.5 text-amber-300" />,
  },
  create_lore: {
    color: 'text-emerald-400', bg: 'bg-emerald-950/40', border: 'border-emerald-800/50',
    icon: <Globe className="h-3.5 w-3.5 text-emerald-400" />,
  },
  update_lore: {
    color: 'text-emerald-300', bg: 'bg-emerald-950/30', border: 'border-emerald-700/40',
    icon: <Globe className="h-3.5 w-3.5 text-emerald-300" />,
  },
  create_chapter: {
    color: 'text-indigo-400', bg: 'bg-indigo-950/40', border: 'border-indigo-800/50',
    icon: <FileText className="h-3.5 w-3.5 text-indigo-400" />,
  },
  update_chapter: {
    color: 'text-blue-400', bg: 'bg-blue-950/40', border: 'border-blue-800/50',
    icon: <FileText className="h-3.5 w-3.5 text-blue-400" />,
  },
  create_timeline_event: {
    color: 'text-purple-400', bg: 'bg-purple-950/40', border: 'border-purple-800/50',
    icon: <Calendar className="h-3.5 w-3.5 text-purple-400" />,
  },
  ask_user: {
    color: 'text-yellow-400', bg: 'bg-yellow-950/40', border: 'border-yellow-800/50',
    icon: <HelpCircle className="h-3.5 w-3.5 text-yellow-400" />,
  },
  read_chapter: {
    color: 'text-slate-400', bg: 'bg-slate-900', border: 'border-slate-700',
    icon: <FileText className="h-3.5 w-3.5 text-slate-400" />,
  },
  read_characters: {
    color: 'text-slate-400', bg: 'bg-slate-900', border: 'border-slate-700',
    icon: <User className="h-3.5 w-3.5 text-slate-400" />,
  },
  read_lore: {
    color: 'text-slate-400', bg: 'bg-slate-900', border: 'border-slate-700',
    icon: <Globe className="h-3.5 w-3.5 text-slate-400" />,
  },
  read_timeline: {
    color: 'text-slate-400', bg: 'bg-slate-900', border: 'border-slate-700',
    icon: <Calendar className="h-3.5 w-3.5 text-slate-400" />,
  },
  read_project_summary: {
    color: 'text-slate-400', bg: 'bg-slate-900', border: 'border-slate-700',
    icon: <Bot className="h-3.5 w-3.5 text-slate-400" />,
  },
  analyze_consistency: {
    color: 'text-orange-400', bg: 'bg-orange-950/30', border: 'border-orange-800/40',
    icon: <Search className="h-3.5 w-3.5 text-orange-400" />,
  },
  search_content: {
    color: 'text-cyan-400', bg: 'bg-cyan-950/30', border: 'border-cyan-800/40',
    icon: <Search className="h-3.5 w-3.5 text-cyan-400" />,
  },
  generate_text: {
    color: 'text-slate-400', bg: 'bg-slate-900', border: 'border-slate-700',
    icon: <Sparkles className="h-3.5 w-3.5 text-slate-400" />,
  },
}

function getToolMeta(tool: string) {
  return TOOL_META[tool] ?? TOOL_META['generate_text']
}

// ── Result summary renderer ───────────────────────────────────────────────────

function ResultFields({
  tool,
  result,
  onInsert,
}: {
  tool: string
  result: Record<string, any>
  onInsert?: (text: string) => void
}) {
  if (result.error) {
    return <p className="text-xs text-red-400">Error: {String(result.error)}</p>
  }
  if (tool === 'create_character' || tool === 'update_character') {
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        {result.name && <p><span className="text-slate-500">Name:</span> {String(result.name)}</p>}
        {result.role && <p><span className="text-slate-500">Role:</span> {String(result.role)}</p>}
        {tool === 'update_character' && result.updated && <p className="text-amber-300">✓ Updated</p>}
      </div>
    )
  }
  if (tool === 'create_lore' || tool === 'update_lore') {
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        {result.name && <p><span className="text-slate-500">Name:</span> {String(result.name)}</p>}
        {result.lore_type && <p><span className="text-slate-500">Type:</span> {String(result.lore_type)}</p>}
        {tool === 'update_lore' && result.updated && <p className="text-emerald-300">✓ Updated</p>}
      </div>
    )
  }
  if (tool === 'create_chapter' || tool === 'update_chapter') {
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        {result.title && <p><span className="text-slate-500">Title:</span> {String(result.title)}</p>}
        {result.word_count != null && <p><span className="text-slate-500">Words:</span> {String(result.word_count)}</p>}
        {tool === 'update_chapter' && result.updated && <p className="text-blue-400">✓ Saved</p>}
      </div>
    )
  }
  if (tool === 'create_timeline_event') {
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        {result.title && <p><span className="text-slate-500">Event:</span> {String(result.title)}</p>}
        {result.event_date && <p><span className="text-slate-500">Date:</span> {String(result.event_date)}</p>}
      </div>
    )
  }
  if (tool === 'ask_user') {
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        {result.answer
          ? <p><span className="text-slate-500">Answer:</span> {String(result.answer)}</p>
          : <p className="text-slate-600 italic">No answer received</p>}
      </div>
    )
  }
  if (tool === 'read_chapter') {
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        {result.title && <p><span className="text-slate-500">Title:</span> {String(result.title)}</p>}
        {result.word_count != null && <p><span className="text-slate-500">Words:</span> {String(result.word_count)}</p>}
      </div>
    )
  }
  if (tool === 'read_characters') {
    const chars = result.characters as Array<{ name: string }> | undefined
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        <p><span className="text-slate-500">Found:</span> {String(result.count)} character(s)</p>
        {chars && chars.length > 0 && (
          <p className="text-slate-500">{chars.slice(0, 4).map((c) => c.name).join(', ')}{chars.length > 4 ? '…' : ''}</p>
        )}
      </div>
    )
  }
  if (tool === 'read_lore') {
    const items = result.lore as Array<{ name: string }> | undefined
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        <p><span className="text-slate-500">Found:</span> {String(result.count)} lore item(s)</p>
        {items && items.length > 0 && (
          <p className="text-slate-500">{items.slice(0, 4).map((i) => i.name).join(', ')}{items.length > 4 ? '…' : ''}</p>
        )}
      </div>
    )
  }
  if (tool === 'read_timeline') {
    const events = result.events as Array<{ title: string }> | undefined
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        <p><span className="text-slate-500">Found:</span> {String(result.count)} event(s)</p>
        {events && events.length > 0 && (
          <p className="text-slate-500">{events.slice(0, 3).map((e) => e.title).join(', ')}{events.length > 3 ? '…' : ''}</p>
        )}
      </div>
    )
  }
  if (tool === 'search_content') {
    const hits = result.results as Array<{ title: string; kind: string }> | undefined
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        <p><span className="text-slate-500">Query:</span> {String(result.query)}</p>
        <p><span className="text-slate-500">Found:</span> {String(result.count)} result(s)</p>
        {hits && hits.length > 0 && (
          <p className="text-slate-500">
            {hits.slice(0, 4).map((h) => `${h.title} (${h.kind})`).join(', ')}
            {hits.length > 4 ? '…' : ''}
          </p>
        )}
      </div>
    )
  }
  if (tool === 'analyze_consistency') {
    const report = String(result.report ?? '')
    return (
      <div className="space-y-1.5">
        <p className="text-xs text-slate-400 leading-relaxed">
          {report.slice(0, 200)}{report.length > 200 ? '…' : ''}
        </p>
        {onInsert && report && (
          <button
            type="button"
            onClick={() => onInsert(report)}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors"
          >
            <ClipboardCopy className="h-3 w-3" />
            Chèn vào editor
          </button>
        )}
      </div>
    )
  }
  if (tool === 'read_project_summary') {
    return (
      <div className="text-xs text-slate-300 space-y-0.5">
        {result.title && <p><span className="text-slate-500">Project:</span> {String(result.title)}</p>}
        {result.chapter_count != null && <p><span className="text-slate-500">Chapters:</span> {String(result.chapter_count)}</p>}
      </div>
    )
  }
  if (tool === 'generate_text' && result.text) {
    const text = String(result.text)
    const preview = text.slice(0, 120)
    return (
      <div className="space-y-1.5">
        <p className="text-xs text-slate-400 italic">{preview}{text.length > 120 ? '…' : ''}</p>
        {onInsert && (
          <button
            type="button"
            onClick={() => onInsert(text)}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors"
          >
            <ClipboardCopy className="h-3 w-3" />
            Chèn vào editor
          </button>
        )}
      </div>
    )
  }
  if (result.updated) {
    return <p className="text-xs text-slate-400">Updated.</p>
  }
  return null
}

// ── Progress bar ──────────────────────────────────────────────────────────────

function ProgressBar({ completed, total }: { completed: number; total: number }) {
  if (total === 0) return null
  const pct = Math.round((completed / total) * 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] text-slate-500">
        <span>{completed}/{total} steps</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

// ── Preset quick-tasks ────────────────────────────────────────────────────────

function PresetList({ onSelect, chapterTitle }: { onSelect: (task: string) => void; chapterTitle?: string | null }) {
  const [open, setOpen] = useState(false)
  const presets = getPresets(chapterTitle)
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-md border border-slate-800 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-400 hover:bg-slate-800"
      >
        <span>Gợi ý nhanh</span>
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>
      {open && (
        <div className="mt-1 space-y-1">
          {presets.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => { onSelect(p.task); setOpen(false) }}
              className="w-full rounded border border-slate-800 bg-slate-900/60 px-2.5 py-1.5 text-left text-[11px] text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Copy button ───────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }).catch(() => {
      // clipboard unavailable — silently ignore
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

// ── AskUser inline form ───────────────────────────────────────────────────────

function AskUserCard({
  question,
  onAnswer,
}: {
  question: string
  onAnswer: (answer: string) => void
}) {
  const [answer, setAnswer] = useState('')
  const submit = () => {
    if (!answer.trim()) return
    onAnswer(answer.trim())
  }
  return (
    <div className="rounded-lg border border-yellow-800/60 bg-yellow-950/30 p-3 space-y-2">
      <div className="flex items-center gap-1.5">
        <HelpCircle className="h-3.5 w-3.5 text-yellow-400 shrink-0" />
        <span className="text-xs font-semibold text-yellow-400">Agent cần thêm thông tin</span>
      </div>
      <p className="text-xs text-slate-300 leading-relaxed">{question}</p>
      <textarea
        autoFocus
        className="w-full resize-none rounded border border-slate-700 bg-slate-900 p-2 text-xs text-slate-200 placeholder:text-slate-600 focus:border-yellow-700 focus:outline-none"
        rows={2}
        placeholder="Nhập câu trả lời…"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            submit()
          }
        }}
      />
      <button
        type="button"
        onClick={submit}
        disabled={!answer.trim()}
        className="flex w-full items-center justify-center gap-1.5 rounded bg-yellow-700/80 px-3 py-1.5 text-xs font-medium text-yellow-100 hover:bg-yellow-700 disabled:opacity-40"
      >
        <RefreshCw className="h-3 w-3" />
        Trả lời & tiếp tục (Ctrl+Enter)
      </button>
    </div>
  )
}

// ── History panel ─────────────────────────────────────────────────────────────

function HistoryPanel({
  runs,
  onRerun,
  onClear,
  onClose,
}: {
  runs: AgentRun[]
  onRerun: (task: string) => void
  onClear: () => void
  onClose: () => void
}) {
  return (
    <div className="absolute inset-0 z-10 flex flex-col bg-slate-950">
      <header className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-slate-400" />
          <span className="text-sm font-semibold text-slate-200">Lịch sử Agent</span>
        </div>
        <div className="flex items-center gap-1">
          {runs.length > 0 && (
            <button
              type="button"
              onClick={onClear}
              className="rounded px-2 py-1 text-[10px] text-slate-600 hover:bg-slate-800 hover:text-red-400"
            >
              Xóa tất cả
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </header>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {runs.length === 0 ? (
          <p className="text-center text-xs text-slate-600 mt-6">Chưa có lần chạy nào được lưu.</p>
        ) : (
          runs.map((run) => (
            <div
              key={run.id}
              className="rounded-lg border border-slate-800 bg-slate-900 p-3 space-y-1.5"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">{run.task}</p>
                <button
                  type="button"
                  onClick={() => onRerun(run.task)}
                  title="Chạy lại task này"
                  className="shrink-0 rounded px-1.5 py-0.5 text-[10px] text-indigo-400 hover:bg-indigo-900/40 transition-colors"
                >
                  ↺ Chạy lại
                </button>
              </div>
              <p className="text-[10px] text-slate-500 leading-relaxed">{run.summary}</p>
              <div className="flex items-center gap-2 text-[10px] text-slate-600">
                <span>{run.stepsCompleted} bước</span>
                <span>·</span>
                <span>{new Date(run.timestamp).toLocaleString('vi-VN')}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

interface AgentPanelProps {
  projectId?: string | null
  chapterId?: string | null
  chapterTitle?: string | null
  onInsertText?: (text: string) => void
}

export default function AgentPanel({
  projectId: propProjectId,
  chapterId: propChapterId,
  chapterTitle,
  onInsertText,
}: AgentPanelProps) {
  const params = useParams()
  const projectId = propProjectId ?? params.projectId ?? null
  const chapterId = propChapterId ?? null

  const { history, addRun, clearHistory } = useAgentHistory(projectId)
  const [showHistory, setShowHistory] = useState(false)
  const [language, setLanguage] = useState<'vi' | 'en'>('vi')

  const [task, setTask] = useState('')
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('idle')
  const [plan, setPlan] = useState<PlanStep[]>([])
  const [currentStep, setCurrentStep] = useState<{ step: number; description: string } | null>(null)
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())
  const [toolOutputs, setToolOutputs] = useState<ToolOutput[]>([])
  const [streamText, setStreamText] = useState('')
  const [summary, setSummary] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null)

  // Keep task in a ref so the WS done handler can read it without stale closure
  const taskRef = useRef(task)
  useEffect(() => { taskRef.current = task }, [task])

  const wsRef = useRef<WebSocket | null>(null)
  const streamBuf = useRef('')
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [plan, toolOutputs, streamText, summary, agentStatus, pendingQuestion])

  useEffect(() => () => { wsRef.current?.close() }, [])

  const reset = useCallback(() => {
    const ws = wsRef.current
    wsRef.current = null
    ws?.close()
    setAgentStatus('idle')
    setPlan([])
    setCurrentStep(null)
    setCompletedSteps(new Set())
    setToolOutputs([])
    setStreamText('')
    streamBuf.current = ''
    setSummary('')
    setErrorMsg('')
    setPendingQuestion(null)
  }, [])

  const cancel = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'cancel' }))
      wsRef.current.close()
    }
    setAgentStatus('cancelled')
    setPendingQuestion(null)
  }, [])

  const sendAnswer = useCallback((answer: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'answer', answer }))
    }
    setPendingQuestion(null)
    setAgentStatus('running')
  }, [])

  const run = useCallback(() => {
    if (!task.trim() || !projectId) return
    reset()

    setAgentStatus('planning')
    const ws = new WebSocket(wsUrl('/ws/agent'))
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({
        project_id: projectId,
        chapter_id: chapterId ?? '',
        task,
        language,
      }))
    }

    ws.onmessage = (e: MessageEvent) => {
      try {
        const msg = JSON.parse(e.data as string) as Record<string, unknown>
        const type = msg.type as string

        if (type === 'status') {
          setAgentStatus((prev) => prev === 'asking' ? 'asking' : 'planning')
        } else if (type === 'plan') {
          setPlan((msg.steps as PlanStep[]) ?? [])
          setAgentStatus('running')
        } else if (type === 'plan_update') {
          setPlan((msg.steps as PlanStep[]) ?? [])
        } else if (type === 'step_start') {
          setCurrentStep({ step: msg.step as number, description: msg.description as string })
          streamBuf.current = ''
          setStreamText('')
        } else if (type === 'text_delta') {
          streamBuf.current += msg.delta as string
          setStreamText(streamBuf.current)
        } else if (type === 'step_done') {
          setCompletedSteps((prev) => new Set(prev).add(msg.step as number))
          setCurrentStep(null)
          // Capture any streamed text into the result before clearing
          const streamedText = streamBuf.current
          setStreamText('')
          streamBuf.current = ''
          const rawResult = (msg.result as Record<string, unknown>) ?? {}
          // For generate_text: if result.text is empty but we captured streamed text, use it
          const finalResult =
            (msg.tool as string) === 'generate_text' && !rawResult.text && streamedText
              ? { ...rawResult, text: streamedText }
              : rawResult
          setToolOutputs((prev) => [
            ...prev,
            {
              step: msg.step as number,
              tool: msg.tool as string,
              description: msg.description as string,
              result: finalResult,
            },
          ])
        } else if (type === 'ask_user') {
          // Agent is waiting for user input — show inline form
          setAgentStatus('asking')
          setPendingQuestion((msg.question as string) ?? '')
        } else if (type === 'done') {
          const doneSummary = (msg.summary as string) ?? 'Agent completed.'
          const doneSteps = (msg.steps_completed as number) ?? 0
          setSummary(doneSummary)
          setAgentStatus('done')
          addRun(taskRef.current, doneSummary, doneSteps)
          ws.close()
        } else if (type === 'cancelled') {
          setAgentStatus('cancelled')
          ws.close()
        } else if (type === 'error') {
          setErrorMsg((msg.message as string) ?? 'Unknown error')
          setAgentStatus('error')
          ws.close()
        }
      } catch {
        // ignore malformed frames
      }
    }

    ws.onerror = () => {
      setErrorMsg('WebSocket connection failed.')
      setAgentStatus('error')
    }

    ws.onclose = () => {
      setAgentStatus((prev) =>
        prev === 'running' || prev === 'planning' ? 'error' : prev,
      )
    }
  }, [task, projectId, chapterId, language, reset])

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      run()
    }
  }

  const isRunning = agentStatus === 'planning' || agentStatus === 'running' || agentStatus === 'asking'

  return (
    <aside className="relative flex h-full w-80 flex-col bg-slate-950">
      {/* History overlay */}
      {showHistory && (
        <HistoryPanel
          runs={history}
          onRerun={(t) => { setTask(t); setShowHistory(false) }}
          onClear={clearHistory}
          onClose={() => setShowHistory(false)}
        />
      )}

      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-semibold text-slate-200">AI Agent</span>
          {(agentStatus === 'planning' || agentStatus === 'running') && (
            <Zap className="h-3.5 w-3.5 animate-pulse text-yellow-400" />
          )}
          {agentStatus === 'asking' && (
            <HelpCircle className="h-3.5 w-3.5 animate-pulse text-yellow-400" />
          )}
        </div>
        <div className="flex items-center gap-1">
          {/* Language selector */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as 'vi' | 'en')}
            disabled={isRunning}
            className="rounded border border-slate-800 bg-slate-900 px-1.5 py-0.5 text-[10px] text-slate-400 focus:outline-none disabled:opacity-40"
          >
            <option value="vi">VI</option>
            <option value="en">EN</option>
          </select>
          <button
            type="button"
            onClick={() => setShowHistory((v) => !v)}
            title="Lịch sử"
            className="relative rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
          >
            <History className="h-3.5 w-3.5" />
            {history.length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-indigo-400" />
            )}
          </button>
          <button
            onClick={reset}
            title="Reset"
            className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </header>

      {/* Scrollable content */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">

        {/* Idle hint */}
        {agentStatus === 'idle' && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p className="text-xs text-slate-500 leading-relaxed">
              Mô tả nhiệm vụ bằng ngôn ngữ tự nhiên. Agent sẽ tự lập kế hoạch và thực thi.
            </p>
            <p className="mt-2 text-xs text-slate-400 italic">
              "Tạo 3 nhân vật fantasy, viết chương mở đầu, và cập nhật tóm tắt project."
            </p>
          </div>
        )}

        {/* Planning spinner */}
        {agentStatus === 'planning' && (
          <div className="flex items-center gap-2 text-slate-400 text-xs">
            <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
            <span>Đang lập kế hoạch…</span>
          </div>
        )}

        {/* Progress bar */}
        {agentStatus === 'running' && plan.length > 0 && (
          <ProgressBar completed={completedSteps.size} total={plan.length} />
        )}

        {/* Plan overview */}
        {plan.length > 0 && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3 space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              Kế hoạch · {plan.length} bước
            </p>
            {plan.map((s) => {
              const done = completedSteps.has(s.step)
              const active = currentStep?.step === s.step
              const meta = getToolMeta(s.tool)
              return (
                <div key={s.step} className="flex items-start gap-2">
                  {done ? (
                    <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-500" />
                  ) : active ? (
                    <Loader2 className="mt-0.5 h-3.5 w-3.5 shrink-0 animate-spin text-indigo-400" />
                  ) : (
                    <span className="mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center">
                      {meta.icon}
                    </span>
                  )}
                  <span className={`text-xs leading-relaxed ${
                    done ? 'text-slate-500 line-through' : active ? 'text-slate-200' : 'text-slate-400'
                  }`}>
                    {s.description}
                  </span>
                </div>
              )
            })}
          </div>
        )}

        {/* Tool output cards */}
        {toolOutputs.map((out) => {
          const meta = getToolMeta(out.tool)
          return (
            <div key={out.step} className={`rounded-lg border p-3 space-y-1.5 ${meta.bg} ${meta.border}`}>
              <div className="flex items-center gap-1.5">
                {meta.icon}
                <span className={`text-[10px] font-semibold uppercase tracking-wide ${meta.color}`}>
                  {out.tool.replace(/_/g, ' ')}
                </span>
              </div>
              <p className="text-xs text-slate-400">{out.description}</p>
              <ResultFields tool={out.tool} result={out.result} onInsert={onInsertText} />
            </div>
          )
        })}

        {/* Streaming text card */}
        {streamText && (
          <div className="rounded-lg border border-indigo-900/50 bg-indigo-950/30 p-3 space-y-1.5">
            <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-400">
              <Zap className="h-3 w-3" />
              Đang viết…
            </div>
            <p className="whitespace-pre-wrap text-xs leading-relaxed text-slate-300">{streamText}</p>
            <div className="flex gap-1 pt-0.5">
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

        {/* ask_user inline form */}
        {agentStatus === 'asking' && pendingQuestion && (
          <AskUserCard question={pendingQuestion} onAnswer={sendAnswer} />
        )}

        {/* Done */}
        {agentStatus === 'done' && summary && (
          <div className="rounded-lg border border-green-800/50 bg-green-950/40 p-3 space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <CheckCircle className="h-3.5 w-3.5 text-green-400" />
                <span className="text-xs font-semibold text-green-400">Hoàn thành</span>
              </div>
              <CopyButton text={summary} />
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">{summary}</p>
          </div>
        )}

        {/* Cancelled */}
        {agentStatus === 'cancelled' && (
          <div className="rounded-lg border border-yellow-800/50 bg-yellow-950/30 p-3 flex items-center gap-2">
            <Square className="h-3.5 w-3.5 text-yellow-400" />
            <span className="text-xs text-yellow-400">Đã hủy bởi người dùng.</span>
          </div>
        )}

        {/* Error */}
        {agentStatus === 'error' && (
          <div className="rounded-lg border border-red-800/50 bg-red-950/30 p-3 space-y-1">
            <div className="flex items-center gap-1.5">
              <AlertCircle className="h-3.5 w-3.5 text-red-400" />
              <span className="text-xs font-semibold text-red-400">Lỗi</span>
            </div>
            {errorMsg && <p className="text-xs text-slate-400">{errorMsg}</p>}
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-slate-800 p-3 space-y-2">
        {!projectId && (
          <p className="text-center text-xs text-slate-600">Mở project để dùng agent.</p>
        )}
        {agentStatus === 'idle' && projectId && (
          <PresetList onSelect={(t) => setTask(t)} chapterTitle={chapterTitle} />
        )}
        <textarea
          className="h-20 w-full resize-none rounded-md border border-slate-800 bg-slate-900 p-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-700 focus:outline-none disabled:opacity-50"
          placeholder="Mô tả nhiệm vụ… (Ctrl+Enter)"
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={isRunning || !projectId}
        />
        {isRunning ? (
          <button
            type="button"
            onClick={cancel}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-red-900/80 px-3 py-2 text-sm font-medium text-red-200 hover:bg-red-800"
          >
            <Square className="h-3.5 w-3.5" />
            Hủy
          </button>
        ) : (
          <button
            type="button"
            onClick={run}
            disabled={!task.trim() || !projectId}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
          >
            <Play className="h-3.5 w-3.5" />
            Chạy Agent
          </button>
        )}
      </div>
    </aside>
  )
}
