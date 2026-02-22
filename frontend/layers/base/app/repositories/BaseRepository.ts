import type { UseFetchOptions } from '#app'

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

    // Gestion centralisée de la remontée d'erreur vers le composant appelant
    if (error.value) {
      // On throw l'erreur pour qu'elle puisse être catchée par le bloc try/catch du composant
      throw error.value
    }

    return {
      // On garantit que data.value est bien du type TransformT
      data: data.value as TransformT,
      refresh,
      pending,
    }
  }
}
