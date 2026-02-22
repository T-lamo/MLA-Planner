export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface MLANotification {
  id: string
  title: string
  // ... reste de l'interface
  type: NotificationType
}
