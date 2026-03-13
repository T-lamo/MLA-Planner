import type { EnhancedApiError } from '../../types/api'

/**
 * Composable mutualisé pour la gestion des erreurs dans les formulaires.
 *
 * Pattern identique à login.vue :
 * 1. Toast intelligent via useErrorHandler.notifyError
 *    (routing 422 / 500+ / métier / réseau)
 * 2. Message lisible retourné pour l'affichage inline
 * 3. formError — état réactif optionnel pour le binding direct
 */
export const useFormError = () => {
  const { notifyError } = useErrorHandler()
  const formError = ref<string | null>(null)

  function handleError(e: unknown, fallback = 'Une erreur est survenue.'): string {
    const err = e as EnhancedApiError
    notifyError(err)
    const msg = err?.data?.error?.message ?? err?.data?.message ?? fallback
    formError.value = msg
    return msg
  }

  function clearError(): void {
    formError.value = null
  }

  return { formError, handleError, clearError }
}
