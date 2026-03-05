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

/**
 * Logique commune de configuration (Headers, Intercepteurs)
 */
function getApiConfig() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const route = useRoute()
  const { notifyError } = useErrorHandler()

  return {
    baseURL: config.public.apiBase || 'http://localhost:8000',
    onRequest({ options }: RequestInterceptorCtx) {
      if (authStore.token) {
        options.headers = {
          ...options.headers,
          Authorization: `Bearer ${authStore.token}`,
        }
      }
    },
    onResponseError({ response, request }: ResponseErrorInterceptorCtx) {
      const isLoginRequest = request.toString().includes('/auth/token')

      if (response.status === 401 && !isLoginRequest) {
        authStore.logout()
        if (route.path !== '/login') {
          navigateTo({ path: '/login', query: { redirect: route.fullPath } })
        }
        return
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
 * Résout l'erreur "Component is already mounted"
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
