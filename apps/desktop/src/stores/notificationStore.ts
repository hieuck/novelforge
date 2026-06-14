import { create } from 'zustand'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}

interface NotificationStore {
  notifications: Notification[]
  add: (type: Notification['type'], message: string) => void
  remove: (id: string) => void
}

let counter = 0

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],

  add: (type, message) => {
    const id = `notif-${++counter}`
    set((s) => ({ notifications: [...s.notifications, { id, type, message }] }))
    setTimeout(() => {
      set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) }))
    }, 4000)
  },

  remove: (id) => {
    set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) }))
  },
}))
