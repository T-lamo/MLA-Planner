import { onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/useAuthStore'

const REFRESH_BEFORE_EXPIRY_MS = 60_000 // rafraîchir 60s avant expiration

/**
 * Gère le cycle de vie de la session : planifie un refresh silencieux proactif
 * 60 secondes avant l'expiration du token. Le timer se relance automatiquement
 * après chaque refresh réussi. Se nettoie proprement au démontage.
 *
 * Dégradation gracieuse : si refreshToken est null, aucun timer n'est armé.
 */
export function useSessionManager() {
  const authStore = useAuthStore()
  let timer: ReturnType<typeof setTimeout> | null = null

  function clearTimer() {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  function scheduleRefresh() {
    clearTimer()

    if (!authStore.refreshToken || !authStore.expiresAt) return

    const delay = new Date(authStore.expiresAt).getTime() - Date.now() - REFRESH_BEFORE_EXPIRY_MS

    if (delay <= 0) {
      // Token déjà expiré ou expirant dans moins de 60s — refresh immédiat
      authStore.silentRefresh().then((ok) => {
        if (ok) scheduleRefresh()
      })
      return
    }

    timer = setTimeout(async () => {
      const ok = await authStore.silentRefresh()
      if (ok) scheduleRefresh()
    }, delay)
  }

  onMounted(() => {
    scheduleRefresh()
  })

  onUnmounted(() => {
    clearTimer()
  })
}
