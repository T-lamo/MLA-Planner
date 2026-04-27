import { useAuthStore } from '../stores/useAuthStore'
import { useUIStore } from '~~/layers/base/app/stores/useUiStore'

// middleware/auth.ts
export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore()
  const uiStore = useUIStore()
  const publicRoutes = ['/login', '/register']
  const isPublicRoute = publicRoutes.includes(to.path)

  // 1. Vérification de l'expiration AVANT toute action
  if (authStore.token && !authStore.isAuthenticated) {
    // Le token existe mais est expiré selon le cookie 'auth_expires_at'
    authStore.clearLocalAuth()

    if (!isPublicRoute) {
      return navigateTo({ path: '/login', query: { expired: '1' } }, { replace: true })
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

  // 3. Initialisation du campus actif si l'utilisateur est authentifié et qu'aucun
  //    campus n'est sélectionné (premier chargement ou refresh F5).
  //    Obligatoire avant toute requête nécessitant X-Campus-Id.
  if (authStore.isAuthenticated && !uiStore.selectedCampusId) {
    await uiStore.initializeUI(authStore.currentUser?.campusPrincipalId ?? undefined)
  }

  // 4. Guards de navigation
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
