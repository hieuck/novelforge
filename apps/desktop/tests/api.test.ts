import { describe, it, expect } from 'vitest'
import { wsUrl } from '@/lib/api'
describe('wsUrl', () => {
  it('default port', () => { delete (window as any).__NOVELFORGE__; const u = wsUrl('/ws/ai'); expect(u).toContain('9000'); expect(u).toContain('/api/ws/ai') })
  it('injected port', () => { ;(window as any).__NOVELFORGE__ = { enginePort: 8888 }; expect(wsUrl('/ws/x')).toContain('8888'); delete (window as any).__NOVELFORGE__ })
})
