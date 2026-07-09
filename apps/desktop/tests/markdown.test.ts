import { describe, it, expect } from 'vitest'
import { renderMarkdownToHtml, stripMarkdown } from '../src/lib/markdown'

describe('renderMarkdownToHtml', () => {
  it('renders bold text', () => {
    expect(renderMarkdownToHtml('This is **bold** text.')).toContain('<strong>bold</strong>')
  })

  it('renders italic text', () => {
    expect(renderMarkdownToHtml('This is *italic* text.')).toContain('<em>italic</em>')
  })

  it('renders headings', () => {
    const html = renderMarkdownToHtml('## Section\n\n### Subsection')
    expect(html).toContain('<h2>Section</h2>')
    expect(html).toContain('<h3>Subsection</h3>')
  })

  it('wraps paragraphs', () => {
    expect(renderMarkdownToHtml('First paragraph.\n\nSecond paragraph.')).toContain('<p>')
  })
})

describe('stripMarkdown', () => {
  it('removes bold markers', () => {
    expect(stripMarkdown('**bold**')).toBe('bold')
  })

  it('removes italic markers', () => {
    expect(stripMarkdown('*italic*')).toBe('italic')
  })

  it('removes heading markers', () => {
    expect(stripMarkdown('## Heading')).toBe('Heading')
  })
})
