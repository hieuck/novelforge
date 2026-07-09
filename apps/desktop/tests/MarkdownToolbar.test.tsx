import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MarkdownToolbar } from '@/components/MarkdownToolbar'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}))

function createTextarea(value = '') {
  const ta = document.createElement('textarea')
  ta.value = value
  document.body.appendChild(ta)
  return {
    ref: { current: ta } as React.RefObject<HTMLTextAreaElement>,
    cleanup: () => ta.remove(),
  }
}

describe('MarkdownToolbar', () => {
  it('inserts bold syntax at cursor', () => {
    const { ref, cleanup } = createTextarea('hello world')
    const onChange = vi.fn()
    render(<MarkdownToolbar textareaRef={ref} content="hello world" onContentChange={onChange} />)

    ref.current!.setSelectionRange(6, 11)
    fireEvent.click(screen.getByTitle('editor.bold'))

    expect(onChange).toHaveBeenCalledWith('hello **world**')
    cleanup()
  })

  it('inserts italic syntax at cursor', () => {
    const { ref, cleanup } = createTextarea('hello world')
    const onChange = vi.fn()
    render(<MarkdownToolbar textareaRef={ref} content="hello world" onContentChange={onChange} />)

    ref.current!.setSelectionRange(6, 11)
    fireEvent.click(screen.getByTitle('editor.italic'))

    expect(onChange).toHaveBeenCalledWith('hello *world*')
    cleanup()
  })

  it('inserts heading syntax at cursor line', () => {
    const { ref, cleanup } = createTextarea('world')
    const onChange = vi.fn()
    render(<MarkdownToolbar textareaRef={ref} content="world" onContentChange={onChange} />)

    ref.current!.setSelectionRange(0, 5)
    fireEvent.click(screen.getByTitle('editor.heading_1'))

    expect(onChange).toHaveBeenCalledWith('## world')
    cleanup()
  })
})
