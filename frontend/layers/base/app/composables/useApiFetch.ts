import type { UseFetchOptions } from '#app'
import { defu } from 'defu'
import type { ApiErrorResponse, EnhancedApiError } from '../../types/api'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

export const useApiFetch = <ResT, TransformT = ResT>(
  url: string | (() => string),
  options: UseFetchOptions<ResT, TransformT> = {},
) => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const route = useRoute()
  const { notifyError } = useErrorHandler()

  /**
   * Construction des headers dynamiques.
   * On récupère le token du store à chaque exécution.
   */
  const authHeaders: Record<string, string> = {}
  if (authStore.token) {
    authHeaders.Authorization = `Bearer ${authStore.token}`
  }

  /**
   * Construction des paramètres par défaut
   */

  const defaults: UseFetchOptions<ResT, TransformT> = {
    baseURL: config.public.apiBase || 'http://localhost:8000',

    // Injection initiale des headers
    headers: authHeaders,

    /**
     * Intercepteur de requête : rafraîchit le token juste avant l'envoi
     */
    onRequest({ options }) {
      if (authStore.token) {
        const headers = options.headers as unknown as Record<string, string>
        headers['Authorization'] = `Bearer ${authStore.token}`
      }
    },

    /**
     * Intercepteur d'erreur global
     */
    onResponseError({ response, request }) {
      const isLoginRequest = request.toString().includes('/auth/token')

      // 1. Gestion de la Session (401 Unauthorized)
      if (response.status === 401 && !isLoginRequest) {
        authStore.logout()
        if (route.path !== '/login') {
          navigateTo({
            path: '/login',
            query: { redirect: route.fullPath },
          })
        }
        return
      }

      /**
       * 2. Synchronisation avec MLA Notify
       * EXPERT : On construit l'objet EnhancedApiError attendu par notifyError.
       * Fetch stocke le corps de la réponse d'erreur dans response._data.
       */
      const errorPayload: EnhancedApiError = {
        name: 'ApiError',
        message: response.statusText,
        statusCode: response.status,
        data: response._data as ApiErrorResponse, // C'est ici que se trouve ton {"error": {...}}
      }

      notifyError(errorPayload)
    },
  }

  // Fusion des options utilisateur avec les défauts
  const params = defu(options, defaults)

  return useFetch(url, params)
}
