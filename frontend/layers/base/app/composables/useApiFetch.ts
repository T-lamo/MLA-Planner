import type { UseFetchOptions } from '#app'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

export const useApiFetch = <T>(url: string, options: UseFetchOptions<T> = {}) => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore() // Accessible grâce à l'auto-import du layer auth

  const defaults: UseFetchOptions<T> = {
    baseURL: config.public.apiBase || 'https://api.mla-planning.com',
    key: url,
    headers: authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {},

    onResponseError({ response }) {
      if (response.status === 401) {
        authStore.logout()
        navigateTo('/login')
      }
    },
  }

  return useFetch(url, { ...defaults, ...options })
}
