import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAiStore } from '@/stores/aiStore'

global.fetch = vi.fn()

function mockFetch(data: unknown, status = 200) {
  ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
    ok: status < 400,
    status,
    json: async () => data,
  })
}

function mockFetchError(msg = 'network error') {
  ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error(msg))
}

describe('aiStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAiStore.setState({ messages: [], loading: false })
  })

  // ── addUserMessage ──────────────────────────────────────────────────────────

  it('addUserMessage appends a user message', () => {
    useAiStore.getState().addUserMessage('hello')
    const { messages } = useAiStore.getState()
    expect(messages).toHaveLength(1)
    expect(messages[0].role).toBe('user')
    expect(messages[0].content).toBe('hello')
  })

  it('addUserMessage generates unique ids', () => {
    useAiStore.getState().addUserMessage('a')
    useAiStore.getState().addUserMessage('b')
    const ids = useAiStore.getState().messages.map((m) => m.id)
    expect(new Set(ids).size).toBe(2)
  })

  // ── addAssistantMessage ─────────────────────────────────────────────────────

  it('addAssistantMessage appends an assistant message', () => {
    useAiStore.getState().addAssistantMessage('reply')
    const { messages } = useAiStore.getState()
    expect(messages[0].role).toBe('assistant')
    expect(messages[0].content).toBe('reply')
  })

  // ── clearMessages ───────────────────────────────────────────────────────────

  it('clearMessages empties the list', () => {
    useAiStore.getState().addUserMessage('x')
    useAiStore.getState().clearMessages()
    expect(useAiStore.getState().messages).toHaveLength(0)
  })

  // ── getHistory ──────────────────────────────────────────────────────────────

  it('getHistory returns all messages when under limit', () => {
    useAiStore.getState().addUserMessage('q1')
    useAiStore.getState().addAssistantMessage('a1')
    const history = useAiStore.getState().getHistory()
    expect(history).toHaveLength(2)
    expect(history[0]).toEqual({ role: 'user', content: 'q1' })
    expect(history[1]).toEqual({ role: 'assistant', content: 'a1' })
  })

  it('getHistory caps at 12 messages', () => {
    // Add 8 turns = 16 messages; getHistory should return exactly the last 12
    for (let i = 0; i < 8; i++) {
      useAiStore.getState().addUserMessage(`q${i}`)
      useAiStore.getState().addAssistantMessage(`a${i}`)
    }
    const history = useAiStore.getState().getHistory()
    expect(history).toHaveLength(12)
    // Should be the last 12 messages (turns 2-7)
    expect(history[0].content).toBe('q2')
  })

  it('getHistory returns empty array when no messages', () => {
    expect(useAiStore.getState().getHistory()).toEqual([])
  })

  // ── sendMessage (HTTP fallback) ─────────────────────────────────────────────

  it('sendMessage on success adds user + assistant messages', async () => {
    mockFetch({ result: 'AI says hi' })
    await useAiStore.getState().sendMessage('hi')
    const { messages } = useAiStore.getState()
    expect(messages).toHaveLength(2)
    expect(messages[0].role).toBe('user')
    expect(messages[0].content).toBe('hi')
    expect(messages[1].role).toBe('assistant')
    expect(messages[1].content).toBe('AI says hi')
  })

  it('sendMessage on success sets loading false after completion', async () => {
    mockFetch({ result: 'ok' })
    await useAiStore.getState().sendMessage('test')
    expect(useAiStore.getState().loading).toBe(false)
  })

  it('sendMessage on network error adds error message', async () => {
    mockFetchError('connection refused')
    await useAiStore.getState().sendMessage('test')
    const { messages } = useAiStore.getState()
    expect(messages).toHaveLength(2)
    expect(messages[1].content).toContain('Lỗi')
    expect(useAiStore.getState().loading).toBe(false)
  })

  it('sendMessage on HTTP error adds error message', async () => {
    mockFetch({ detail: 'AI provider error' }, 502)
    await useAiStore.getState().sendMessage('test')
    const { messages } = useAiStore.getState()
    expect(messages[1].content).toContain('Lỗi')
  })

  it('sendMessage with missing result falls back to placeholder', async () => {
    mockFetch({})  // no result field
    await useAiStore.getState().sendMessage('test')
    const { messages } = useAiStore.getState()
    expect(messages[1].content).toBe('[no response]')
  })

  it('sendMessage passes action and meta to API', async () => {
    mockFetch({ result: 'done' })
    await useAiStore
      .getState()
      .sendMessage('text', { action: 'rewrite', projectId: 'p1', chapterId: 'c1' })
    const call = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    const body = JSON.parse(call[1].body as string)
    expect(body.action).toBe('rewrite')
    expect(body.project_id).toBe('p1')
    expect(body.chapter_id).toBe('c1')
    expect(body.text).toBe('text')
  })

  it('sendMessage sends history snapshot from before current message', async () => {
    // Pre-load one turn
    useAiStore.getState().addUserMessage('prior q')
    useAiStore.getState().addAssistantMessage('prior a')

    mockFetch({ result: 'ok' })
    await useAiStore.getState().sendMessage('new q')

    const call = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    const body = JSON.parse(call[1].body as string)
    // history should contain the 2 prior messages, not the current 'new q'
    expect(body.history).toHaveLength(2)
    expect(body.history[0].content).toBe('prior q')
    expect(body.history[1].content).toBe('prior a')
  })
})
