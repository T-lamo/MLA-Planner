import { useMLANotificationStore, type NotificationType } from '../stores/useMLANotificationStore'

const lastFingerprint = ref<string | null>(null)
const LOCK_TIME = 2000

export const useMLANotify = () => {
  const store = useMLANotificationStore()

  const createNotify =
    (type: NotificationType) =>
    (title: string, description?: string, opts = {}) => {
      // Fingerprinting simple pour éviter les doublons
      const fingerprint = `${type}-${title}-${description}`
      if (lastFingerprint.value === fingerprint) return

      lastFingerprint.value = fingerprint
      setTimeout(() => {
        lastFingerprint.value = null
      }, LOCK_TIME)

      return store.push({
        title,
        description,
        type,
        duration: 5000,
        persistent: false,
        ...opts,
      })
    }

  return {
    success: createNotify('success'),
    error: createNotify('error'),
    warning: createNotify('warning'),
    info: createNotify('info'),
    remove: store.remove,
  }
}
