import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore()
  const publicRoutes = ['/login', '/register']
  const isPublicRoute = publicRoutes.includes(to.path)

  // 1. Récupération des cookies pour le check de "Cold Start"
  const token = useCookie('auth_token')
  const expiresAt = useCookie('auth_expires_at')

  // 2. Gestion du rafraîchissement (F5) ou accès direct
  // Si le store est vide mais qu'on a un token potentiellement valide
  if (!authStore.isAuthenticated && token.value && expiresAt.value) {
    // On vérifie si le token n'est pas expiré avant d'appeler l'API
    const now = new Date()
    const expirationDate = new Date(expiresAt.value as string)

    if (now < expirationDate) {
      await authStore.fetchMe()
    } else {
      // Si expiré, on nettoie tout de suite
      await authStore.logout(false, to.path)
    }
  }

  // 3. CAS : Route Publique (/login, /register)
  if (isPublicRoute) {
    // Si l'utilisateur est authentifié, on lui interdit l'accès au login -> Home
    if (authStore.isAuthenticated) {
      return navigateTo('/')
    }
    // Sinon, on le laisse accéder à la page publique
    return
  }

  // 4. CAS : Route Protégée
  // Si après toutes les vérifications, l'utilisateur n'est toujours pas connecté
  if (!authStore.isAuthenticated) {
    return navigateTo(
      {
        path: '/login',
        query: { redirect: to.fullPath },
      },
      {
        replace: true,
      },
    )
  }
})
