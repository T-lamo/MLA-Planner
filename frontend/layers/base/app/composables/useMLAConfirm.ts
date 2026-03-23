import { useMLANotificationStore } from '../stores/useMLANotificationStore'

export const useMLAConfirm = () => {
  const store = useMLANotificationStore()

  /**
   * Affiche une notification persistante avec boutons Confirmer / Annuler.
   * Retourne une Promise<boolean> qui se résout quand l'utilisateur choisit.
   * Résout false si la notification est fermée via le bouton ×.
   */
  function confirm(title: string, description?: string): Promise<boolean> {
    return new Promise((resolve) => {
      let resolved = false

      const doResolve = (value: boolean) => {
        if (resolved) return
        resolved = true
        resolve(value)
      }

      store.push({
        type: 'warning',
        title,
        description,
        duration: 0,
        persistent: true,
        _onRemove: () => doResolve(false),
        actions: [
          {
            label: 'Confirmer',
            variant: 'danger',
            onClick: () => doResolve(true),
          },
          {
            label: 'Annuler',
            variant: 'ghost',
            onClick: () => doResolve(false),
          },
        ],
      })
    })
  }

  return { confirm }
}
