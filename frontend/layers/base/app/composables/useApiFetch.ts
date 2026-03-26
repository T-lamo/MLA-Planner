import { defu } from 'defu'
import type { NitroFetchOptions, NitroFetchRequest } from 'nitropack'
import type { ApiErrorResponse, EnhancedApiError } from '../../types/api'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

interface RequestInterceptorCtx {
  options: { headers?: Record<string, string> }
}

interface ResponseErrorInterceptorCtx {
  response: { status: number; statusText: string; _data: unknown }
  request: { toString(): string }
}

// Flag module-level pour éviter les boucles de refresh concurrentes
let _isRefreshing = false

/**
 * Logique commune de configuration (Headers, Intercepteurs)
 */
function getApiConfig() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const route = useRoute()
  const { notifyError } = useErrorHandler()

  // Côté serveur (Nitro), on utilise la variable privée pour atteindre le backend
  // via le réseau interne Docker (http://backend:8000) plutôt que localhost.
  const baseURL = import.meta.server
    ? config.apiBase || config.public.apiBase || 'http://localhost:8000'
    : config.public.apiBase || 'http://localhost:8000'

  return {
    baseURL,
    onRequest({ options }: RequestInterceptorCtx) {
      if (authStore.token) {
        options.headers = {
          ...options.headers,
          Authorization: `Bearer ${authStore.token}`,
        }
      }
    },
    async onResponseError({ response, request }: ResponseErrorInterceptorCtx) {
      const url = request.toString()
      const isLoginRequest = url.includes('/auth/token')
      const isRefreshRequest = url.includes('/auth/refresh')

      if (response.status === 401 && !isLoginRequest && !isRefreshRequest) {
        // Tentative de refresh silencieux (une seule fois, pas de boucle)
        if (!_isRefreshing) {
          _isRefreshing = true
          try {
            const ok = await authStore.silentRefresh()
            if (!ok) {
              authStore.logout()
              if (route.path !== '/login') {
                navigateTo({ path: '/login', query: { redirect: route.fullPath } })
              }
            }
          } finally {
            _isRefreshing = false
          }
        }
        return
      }

      // 403 : le rôle a peut-être expiré depuis la dernière connexion (RBAC-1).
      // Re-sync silencieux des droits → les computed canManagePlanning / hasAdminAccess
      // se mettront à jour réactivement et masqueront les boutons non autorisés.
      if (response.status === 403 && !isLoginRequest) {
        await authStore.fetchMe().catch(() => {})
      }

      const errorPayload: EnhancedApiError = {
        name: 'ApiError',
        message: response.statusText,
        statusCode: response.status,
        data: response._data as ApiErrorResponse,
      }
      notifyError(errorPayload)
    },
  }
}

/**
 * Utilitaire pour les appels IMPÉRATIFS (Actions, Repositories, Watchers)
 */
export const $api = <T>(url: string, options: NitroFetchOptions<NitroFetchRequest> = {}) => {
  const defaults = getApiConfig()
  const params = defu(options, defaults)
  return $fetch<T>(url, params as Parameters<typeof $fetch>[1])
}

/**
 * Utilitaire pour le SETUP des composants (Rendu initial SSR/Client)
 */
export const useApi = <ResT, TransformT = ResT>(
  url: string | (() => string),
  options: Record<string, unknown> = {},
) => {
  const defaults = getApiConfig()
  const params = defu(options, defaults)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return useFetch<ResT, TransformT>(url, params as any)
}
