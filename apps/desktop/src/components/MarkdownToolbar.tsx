import { Bold, Italic, Heading1, Heading2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface MarkdownToolbarProps {
  textareaRef: React.RefObject<HTMLTextAreaElement | null>
  content: string
  onContentChange: (value: string) => void
}

export function MarkdownToolbar({ textareaRef, content, onContentChange }: MarkdownToolbarProps) {
  const { t } = useTranslation()
  const ta = textareaRef.current

  const wrap = (before: string, after: string) => {
    if (!ta) return
    const start = ta.selectionStart ?? 0
    const end = ta.selectionEnd ?? 0
    const selected = content.slice(start, end)
    const replacement = `${before}${selected || ''}${after}`
    const next = content.slice(0, start) + replacement + content.slice(end)
    onContentChange(next)
    // Restore focus and place cursor after the wrapped text
    requestAnimationFrame(() => {
      ta.focus()
      const cursor = start + before.length + selected.length
      ta.setSelectionRange(cursor, cursor)
    })
  }

  const linePrefix = (prefix: string) => {
    if (!ta) return
    const start = ta.selectionStart ?? 0
    const lineStart = content.lastIndexOf('\n', start - 1) + 1
    const next = content.slice(0, lineStart) + prefix + content.slice(lineStart)
    onContentChange(next)
    requestAnimationFrame(() => {
      ta.focus()
      const cursor = lineStart + prefix.length
      ta.setSelectionRange(cursor, cursor)
    })
  }

  const tools = [
    { icon: Bold, title: t('editor.bold'), action: () => wrap('**', '**') },
    { icon: Italic, title: t('editor.italic'), action: () => wrap('*', '*') },
    { icon: Heading1, title: t('editor.heading_1'), action: () => linePrefix('## ') },
    { icon: Heading2, title: t('editor.heading_2'), action: () => linePrefix('### ') },
  ]

  return (
    <div className="flex items-center gap-1 border-b border-slate-800/70 bg-slate-950 px-2 py-1">
      {tools.map(({ icon: Icon, title, action }) => (
        <button
          key={title}
          type="button"
          title={title}
          onClick={action}
          className="rounded p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
        >
          <Icon className="h-4 w-4" />
        </button>
      ))}
    </div>
  )
}
