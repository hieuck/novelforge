import { useState } from 'react'

interface Props {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void | Promise<void>
  onCancel: () => void
}

export default function ConfirmDialog({ open, title, message, confirmLabel = 'Xóa', cancelLabel = 'Hủy', onConfirm, onCancel }: Props) {
  const [busy, setBusy] = useState(false)
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onCancel}>
      <div className="w-80 rounded-lg border border-slate-700 bg-slate-900 p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
        <p className="mt-2 text-xs text-slate-400">{message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onCancel} className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500">
            {cancelLabel}
          </button>
          <button onClick={async () => { setBusy(true); try { await onConfirm() } finally { setBusy(false) } }}
            disabled={busy}
            className="rounded-md bg-red-700 px-3 py-1.5 text-xs text-white hover:bg-red-600 disabled:opacity-50">
            {busy ? 'Đang xóa...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
