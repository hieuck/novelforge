import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import i18n from '../i18n'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children
    if (this.props.fallback) return this.props.fallback

    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
        <AlertTriangle className="h-10 w-10 text-red-400" />
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{i18n.t('error_boundary.title')}</h2>
          <p className="mt-1 max-w-sm text-sm text-slate-400">
            {this.state.error?.message ?? i18n.t('error_boundary.unknown')}
          </p>
        </div>
        <button
          onClick={() => this.setState({ hasError: false, error: null })}
          className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-slate-500 hover:text-slate-100"
        >
          {i18n.t('error_boundary.retry')}
        </button>
      </div>
    )
  }
}
