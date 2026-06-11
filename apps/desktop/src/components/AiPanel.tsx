import { useState } from 'react'
import { useAiStore } from '../stores/aiStore'
import { useChapterStore } from '../stores/chapterStore'
import { useParams } from 'react-router-dom'

export default function AiPanel() {
  const { projectId } = useParams()
  const { messages, loading, sendMessage } = useAiStore()
  const { activeChapterId } = useChapterStore()
  const [input, setInput] = useState('')

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    await sendMessage(input, { projectId: projectId, chapterId: activeChapterId, action: 'continue' })
    setInput('')
  }

  return (
    <aside className="flex h-full flex-col border-l border-slate-800/70 bg-slate-900/40">
      <header className="border-b border-slate-800/70 px-4 py-2">
        <div className="text-sm font-semibold text-slate-200">AI Assistant</div>
        <div className="text-xs text-slate-500">Context-aware writing helper</div>
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto p-3 text-sm">
        {messages.map((m) => (
          <div key={m.id} className={`rounded-md p-2 ${m.role === 'user' ? 'bg-slate-800 text-slate-100' : 'bg-slate-900/60 text-slate-200'}`}>
            <div className="mb-1 text-xs text-slate-500">{m.role}</div>
            <div className="whitespace-pre-wrap">{m.content}</div>
          </div>
        ))}
        {!messages.length && <div className="text-xs text-slate-500">No messages yet.</div>}
      </div>
      <form onSubmit={onSubmit} className="border-t border-slate-800/70 p-3">
        <textarea
          className="mb-2 h-24 w-full rounded-md bg-slate-800 p-2 text-sm"
          placeholder="Ask AI to continue, rewrite, or summarize..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-900"
        >
          {loading ? 'Đang tạo...' : 'Gửi'}
        </button>
      </form>
    </aside>
  )
}
