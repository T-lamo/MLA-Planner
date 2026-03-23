import { useAuthStore } from '../stores/useAuthStore'

export default defineNuxtRouteMiddleware((to) => {
  if (!to.path.startsWith('/admin')) return

  const authStore = useAuthStore()

  if (!authStore.hasAdminAccess) {
    return navigateTo('/', { replace: true })
  }

  const superAdminOnlyPaths = ['/admin/campuses', '/admin/campus-config', '/admin/super']
  if (superAdminOnlyPaths.some((p) => to.path.startsWith(p))) {
    if (!authStore.isSuperAdmin) {
      return navigateTo('/admin/profiles', { replace: true })
    }
  }
})
