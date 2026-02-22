import type { UseFetchOptions } from '#app'
import { defu } from 'defu'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

export const useApiFetch = <ResT, TransformT = ResT>(
  url: string | (() => string),
  options: UseFetchOptions<ResT, TransformT> = {},
) => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const route = useRoute()

  /**
   * Construction des headers dynamiques.
   * On récupère le token du store à chaque exécution.
   */
  const authHeaders: Record<string, string> = {}
  if (authStore.token) {
    authHeaders.Authorization = `Bearer ${authStore.token}`
  }

  const defaults: UseFetchOptions<ResT, TransformT> = {
    baseURL: config.public.apiBase || 'http://localhost:8000',

    // On injecte les headers d'authentification
    headers: authHeaders,

    /**
     * Intercepteur de requête :
     * Permet d'injecter des headers de dernière minute ou logiques complexes
     */
    onRequest({ options }) {
      // 1. On s'assure que options.headers existe
      options.headers = options.headers || {}

      if (authStore.token) {
        // 2. La solution "Double Cast" recommandée par TS pour les types Headers incompatibles :
        // On passe par 'unknown' pour forcer la conversion en Record
        const headers = options.headers as unknown as Record<string, string>
        headers['Authorization'] = `Bearer ${authStore.token}`
      }
    },

    /**
     * Intercepteur d'erreur global
     */
    onResponseError({ response, request }) {
      const isLoginRequest = request.toString().includes('/auth/token')

      if (response.status === 401 && !isLoginRequest) {
        authStore.logout()

        if (route.path !== '/login') {
          navigateTo({
            path: '/login',
            query: { redirect: route.fullPath },
          })
        }
      }

      if (response.status === 422) {
        // console.error('[API Validation Error]:', response._data)
      }

      if (response.status === 403) {
        // console.error('[API Forbidden]: Droits insuffisants.')
      }
    },
  }

  // defu fusionne les options.
  // Attention : l'ordre est important, 'options' (utilisateur) écrase 'defaults'
  const params = defu(options, defaults)

  return useFetch(url, params)
}
