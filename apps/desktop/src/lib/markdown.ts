export function renderMarkdownToHtml(text: string): string {
  const lines = text.split('\n')
  const out: string[] = []
  const buffer: string[] = []

  const inline = (s: string): string =>
    s
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')

  const flush = () => {
    if (buffer.length) {
      out.push(`<p>${inline(buffer.join(' '))}</p>`)
      buffer.length = 0
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    if (!line.trim()) {
      flush()
      continue
    }
    if (line.startsWith('### ')) {
      flush()
      out.push(`<h3>${inline(line.slice(4).trim())}</h3>`)
    } else if (line.startsWith('## ')) {
      flush()
      out.push(`<h2>${inline(line.slice(3).trim())}</h2>`)
    } else {
      buffer.push(line)
    }
  }
  flush()
  return out.join('\n')
}

export function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/^###\s*/gm, '')
    .replace(/^##\s*/gm, '')
}
