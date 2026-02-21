import { useAuthStore } from '../stores/useAuthStore'

export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()
  const publicRoutes = ['/login', '/register']

  if (publicRoutes.includes(to.path)) return

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
