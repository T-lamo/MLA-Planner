// Structure interne envoyée par ton API
export interface ApiErrorDetail {
  code: string
  message: string
  status: number
  detail?: string
}

// Réponse globale de l'API
export interface ApiErrorResponse {
  error?: ApiErrorDetail // Cas de ton AUTH_001
  code?: string // Fallback structure plate
  message?: string
  detail?: string // Fallback FastAPI
  status?: number
}

export interface EnhancedApiError extends Error {
  data?: ApiErrorResponse
  statusCode?: number // Injecté par Nuxt/ofetch (le code HTTP réel)
}
