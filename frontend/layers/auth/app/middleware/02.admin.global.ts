import { useAuthStore } from '../stores/useAuthStore'

export default defineNuxtRouteMiddleware((to) => {
  if (!to.path.startsWith('/admin')) return

  const authStore = useAuthStore()

  if (!authStore.hasAdminAccess) {
    return navigateTo('/', { replace: true })
  }
})
