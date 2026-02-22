import { defineStore } from 'pinia'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface MLANotification {
  id: string
  title: string
  description?: string
  type: NotificationType
  duration: number
  persistent: boolean
  isPaused?: boolean
  _timer?: ReturnType<typeof setTimeout>
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

    // 1. On récupère la référence
    const notification = notifications.value[index]

    // 2. On vérifie explicitement que la notification existe
    // Cela rassure TypeScript sur le fait que 'notification' n'est pas undefined
    if (notification) {
      if (notification._timer) {
        clearTimeout(notification._timer)
      }
      notifications.value.splice(index, 1)
    }
  }
  return { notifications, push, remove, pauseTimer, resumeTimer }
})
