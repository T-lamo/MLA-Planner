import { useAuthStore } from '../stores/useAuthStore'

export default defineNuxtPlugin(async (_nuxtApp) => {
  const authStore = useAuthStore()

  // On exécute l'initialisation une seule fois au démarrage
  // Cela remplit le store avec l'utilisateur si le token est valide
  await authStore.initAuth()
})
