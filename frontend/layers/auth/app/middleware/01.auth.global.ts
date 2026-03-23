import { useAuthStore } from '../stores/useAuthStore'

// middleware/auth.ts
export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore()
  const publicRoutes = ['/login', '/register']
  const isPublicRoute = publicRoutes.includes(to.path)

  // 1. Vérification de l'expiration AVANT toute action
  if (authStore.token && !authStore.isAuthenticated) {
    // Le token existe mais est expiré selon le cookie 'auth_expires_at'
    authStore.clearLocalAuth()

    if (!isPublicRoute) {
      // ✅ CORRECT : La query est dans l'objet de destination (1er argument)
      return navigateTo(
        {
          path: '/login',
          query: { expired: '1' }, // Note: les valeurs de query doivent être des strings idéalement
        },
        {
          replace: true, // Optionnel : remplace l'entrée dans l'historique
        },
      )
    }
  }

  // 2. Hydratation du user si on est authentifié mais que le store est vide (Refresh F5)
  if (authStore.isAuthenticated && !authStore.user) {
    try {
      await authStore.fetchMe()
    } catch {
      // Si fetchMe échoue (ex: 401), le store appellera logout() et cassera la boucle
      return navigateTo('/login')
    }
  }

  // 3. Guards de navigation
  if (isPublicRoute && authStore.isAuthenticated) {
    return navigateTo(authStore.isSuperAdmin ? '/admin/campuses' : '/planning/calendar')
  }

  if (!isPublicRoute && !authStore.isAuthenticated) {
    return navigateTo({
      path: '/login',
      query: { redirect: to.fullPath },
    })
  }
})
