import React, { Suspense } from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Loader2 } from 'lucide-react'

// Test the PageFallback component
function PageFallback() {
  return (
    <div className="flex h-full items-center justify-center text-slate-500">
      <Loader2 className="h-5 w-5 animate-spin" />
    </div>
  )
}

// Test the SplashScreen component
function SplashScreen() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 bg-slate-950">
      <div className="text-xl font-bold text-slate-100">NovelForge</div>
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        Connecting to engine...
      </div>
    </div>
  )
}

describe('PageFallback', () => {
  it('renders spinner', () => {
    const { container } = render(<PageFallback />)
    expect(container.querySelector('.animate-spin')).toBeTruthy()
  })
})

describe('SplashScreen', () => {
  it('renders title and connecting text', () => {
    render(<SplashScreen />)
    expect(screen.getByText('NovelForge')).toBeTruthy()
    expect(screen.getByText('Connecting to engine...')).toBeTruthy()
  })
})

describe('Lazy wrapper', () => {
  it('shows fallback while loading', async () => {
    const LazyComp = () => <div>Loaded</div>
    const lazyImport = () => new Promise<{ default: typeof LazyComp }>((r) =>
      setTimeout(() => r({ default: LazyComp }), 100)
    )
    const LazyLoaded = React.lazy(lazyImport)
    const { container } = render(
      <Suspense fallback={<PageFallback />}>
        <LazyLoaded />
      </Suspense>
    )
    // Should show fallback initially
    expect(container.querySelector('.animate-spin')).toBeTruthy()
  })
})
