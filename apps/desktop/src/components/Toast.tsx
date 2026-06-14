import { X } from 'lucide-react'
import { useNotificationStore } from '../stores/notificationStore'

const ICON = { success: '✓', error: '✕', info: 'i' }
const COLOR = { success: 'border-green-800/60 bg-green-950/40 text-green-300', error: 'border-red-800/60 bg-red-950/40 text-red-300', info: 'border-blue-800/60 bg-blue-950/40 text-blue-300' }

export default function ToastContainer() {
  const { notifications, remove } = useNotificationStore()
  if (!notifications.length) return null

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2">
      {notifications.map((n) => (
        <div key={n.id} className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm shadow-xl ${COLOR[n.type]}`}>
          <span className="font-mono text-xs">{ICON[n.type]}</span>
          <span className="flex-1">{n.message}</span>
          <button onClick={() => remove(n.id)} className="ml-2 opacity-60 hover:opacity-100">
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}
    </div>
  )
}
