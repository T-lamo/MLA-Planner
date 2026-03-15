import { defineStore } from 'pinia'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface NotificationAction {
  label: string
  variant?: 'primary' | 'danger' | 'ghost'
  onClick: () => void
}

export interface MLANotification {
  id: string
  title: string
  description?: string
  type: NotificationType
  duration: number
  persistent: boolean
  isPaused?: boolean
  actions?: NotificationAction[]
  _timer?: ReturnType<typeof setTimeout>
  _onRemove?: () => void
}

export const useMLANotificationStore = defineStore('mla-notifications', () => {
  const notifications = ref<MLANotification[]>([])

  const push = (notification: Omit<MLANotification, 'id'>) => {
    const id = crypto.randomUUID()
    const newNotif = reactive({ ...notification, id, isPaused: false })
    notifications.value.push(newNotif)

    if (!newNotif.persistent) {
      startTimer(newNotif)
    }
    return id
  }

  const startTimer = (notif: MLANotification) => {
    if (notif.persistent) return
    notif._timer = setTimeout(() => remove(notif.id), notif.duration)
  }

  const pauseTimer = (id: string) => {
    const notif = notifications.value.find((n) => n.id === id)
    if (notif?._timer) {
      clearTimeout(notif._timer)
      notif.isPaused = true
    }
  }

  const resumeTimer = (id: string) => {
    const notif = notifications.value.find((n) => n.id === id)
    if (notif && notif.isPaused) {
      notif.isPaused = false
      startTimer(notif)
    }
  }

  const remove = (id: string) => {
    const index = notifications.value.findIndex((n) => n.id === id)
    const notification = notifications.value[index]
    if (notification) {
      if (notification._timer) {
        clearTimeout(notification._timer)
      }
      if (notification._onRemove) {
        notification._onRemove()
      }
      notifications.value.splice(index, 1)
    }
  }
  return { notifications, push, remove, pauseTimer, resumeTimer }
})
