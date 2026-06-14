import { describe, it, expect } from 'vitest'
import { vi, en } from '@novelforge/shared'

type TranslationSet = Record<string, string | Record<string, string>>

function flattenKeys(obj: TranslationSet, prefix = ''): string[] {
  const keys: string[] = []
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (typeof v === 'string') keys.push(key)
    else keys.push(...flattenKeys(v as TranslationSet, key))
  }
  return keys
}

describe('i18n locale files', () => {
  const viKeys = flattenKeys(vi as TranslationSet)
  const enKeys = flattenKeys(en as TranslationSet)

  it('vi.json has same top-level keys as en.json', () => {
    const viTopLevel = Object.keys(vi).sort()
    const enTopLevel = Object.keys(en).sort()
    expect(viTopLevel).toEqual(enTopLevel)
  })

  it('all vi keys exist in en', () => {
    const missing = viKeys.filter((k) => !enKeys.includes(k))
    expect(missing).toEqual([])
  })

  it('all en keys exist in vi', () => {
    const missing = enKeys.filter((k) => !viKeys.includes(k))
    expect(missing).toEqual([])
  })

  it('vi.json has no empty string values', () => {
    const emptyValues: string[] = []
    function checkEmpty(obj: TranslationSet, prefix = '') {
      for (const [k, v] of Object.entries(obj)) {
        const key = prefix ? `${prefix}.${k}` : k
        if (typeof v === 'string') { if (!v) emptyValues.push(key) }
        else checkEmpty(v as TranslationSet, key)
      }
    }
    checkEmpty(vi as TranslationSet)
    expect(emptyValues).toEqual([])
  })

  it('en.json has no empty string values', () => {
    const emptyValues: string[] = []
    function checkEmpty(obj: TranslationSet, prefix = '') {
      for (const [k, v] of Object.entries(obj)) {
        const key = prefix ? `${prefix}.${k}` : k
        if (typeof v === 'string') { if (!v) emptyValues.push(key) }
        else checkEmpty(v as TranslationSet, key)
      }
    }
    checkEmpty(en as TranslationSet)
    expect(emptyValues).toEqual([])
  })
})
