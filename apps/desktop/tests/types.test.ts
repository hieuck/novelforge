import { describe, it, expect } from 'vitest'
import { AI_ACTIONS } from '@/types/index'

const VALID_GROUPS = ['Viết', 'Phân tích', 'Tạo mới', 'Dịch']

describe('AI_ACTIONS', () => {
  it('contains all original required actions', () => {
    const values = AI_ACTIONS.map((a) => a.value)
    ;['continue', 'rewrite', 'expand', 'grammar', 'outline', 'translate_vi_en', 'translate_en_vi']
      .forEach((r) => expect(values).toContain(r))
  })

  it('contains the 4 new writing actions', () => {
    const values = AI_ACTIONS.map((a) => a.value)
    ;['fix_pacing', 'add_sensory', 'tension_build', 'perspective_shift']
      .forEach((r) => expect(values).toContain(r))
  })

  it('each action has a non-empty label', () => {
    AI_ACTIONS.forEach((a) => expect(a.label.length).toBeGreaterThan(0))
  })

  it('each action has a valid group', () => {
    AI_ACTIONS.forEach((a) => expect(VALID_GROUPS).toContain(a.group))
  })

  it('has at least 23 actions', () => {
    expect(AI_ACTIONS.length).toBeGreaterThanOrEqual(23)
  })

  it('all values are unique', () => {
    const values = AI_ACTIONS.map((a) => a.value)
    expect(new Set(values).size).toBe(values.length)
  })

  it('all labels are unique', () => {
    const labels = AI_ACTIONS.map((a) => a.label)
    expect(new Set(labels).size).toBe(labels.length)
  })

  it('writing group contains the most actions', () => {
    const writingCount = AI_ACTIONS.filter((a) => a.group === 'Viết').length
    const otherMax = Math.max(
      ...VALID_GROUPS.filter((g) => g !== 'Viết').map(
        (g) => AI_ACTIONS.filter((a) => a.group === g).length,
      ),
    )
    expect(writingCount).toBeGreaterThan(otherMax)
  })

  it('translate actions are in Dịch group', () => {
    const translateActions = AI_ACTIONS.filter((a) => a.value.startsWith('translate_'))
    expect(translateActions.length).toBe(2)
    translateActions.forEach((a) => expect(a.group).toBe('Dịch'))
  })
})
