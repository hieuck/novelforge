import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { WritingStats } from '@/components/WritingStats'

const mockGet = vi.fn()
vi.mock('@/lib/api', () => ({
  api: {
    get: (...args: any[]) => mockGet(...args),
  },
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}))

describe('WritingStats', () => {
  beforeEach(() => {
    mockGet.mockReset()
  })

  it('renders nothing while loading', () => {
    mockGet.mockImplementation(() => new Promise(() => {}))
    const { container } = render(<WritingStats projectId="p1" />)
    expect(container.innerHTML).toBe('')
  })

  it('renders writing stats after loading', async () => {
    mockGet.mockResolvedValue({
      project_id: 'p1',
      daily_goal: 500,
      today_words: 250,
      total_words: 5000,
      streak: { current: 3, longest: 5 },
      history: [{ date: '2026-07-08', words_added: 250, words_total: 5000 }],
    })

    render(<WritingStats projectId="p1" />)

    await waitFor(() => expect(screen.getByTestId('writing-stats')).toBeTruthy())
    expect(screen.getByTestId('writing-stats-today').textContent).toBe('250')
    expect(screen.getByTestId('writing-stats-goal').textContent).toBe('500')
    expect(screen.getByTestId('writing-stats-streak').textContent).toContain('3')
    expect(screen.getByTestId('writing-stats-progress').textContent).toBe('50%')
    expect(screen.getByTestId('writing-stats-total').textContent).toContain('5,000')
  })

  it('calls the correct endpoint', async () => {
    mockGet.mockResolvedValue({
      project_id: 'p2',
      daily_goal: 1000,
      today_words: 0,
      total_words: 0,
      streak: { current: 0, longest: 0 },
      history: [],
    })

    render(<WritingStats projectId="p2" />)
    await waitFor(() => expect(mockGet).toHaveBeenCalledWith('/projects/p2/writing-stats'))
  })
})
