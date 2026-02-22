import type { UseFetchOptions } from '#app'
import type { EnhancedApiError } from '../../types/api'

/**
 * BaseRepository - Classe abstraite pour centraliser la logique des services API
 * Gère le typage strict entre la réponse brute et la donnée transformée.
 */
export abstract class BaseRepository {
  /**
   * Wrapper interne pour utiliser useApiFetch dans les classes héritées.
   * * @template ResT - Type de la réponse brute (ex: LoginSchema)
   * @template TransformT - Type final après transformation (ex: AuthResponse)
   * * @param url - Endpoint de l'API
   * @param options - Options de configuration Nuxt useFetch
   */
  protected async apiRequest<ResT, TransformT = ResT>(
    url: string | (() => string),
    options?: UseFetchOptions<ResT, TransformT>,
  ) {
    // On propage les deux génériques à useApiFetch pour autoriser le 'transform'
    const { data, error, refresh, pending } = await useApiFetch<ResT, TransformT>(url, options)

    if (error.value) {
      /**
       * CRITÈRE EXPERT : Normalisation de l'erreur
       * On cast l'erreur Fetch en notre type EnhancedApiError.
       * L'intercepteur dans useApiFetch a déjà déclenché le Toast,
       * mais on "throw" pour permettre au composant de gérer sa logique locale (ex: stop loader).
       */
      const apiError = error.value as unknown as EnhancedApiError

      // On enrichit l'erreur si besoin avant de la lancer
      throw apiError
    }
    return {
      // On garantit que data.value est bien du type TransformT
      data: data.value as TransformT,
      refresh,
      pending,
    }
  }
}
