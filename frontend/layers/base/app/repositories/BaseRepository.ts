import type { NitroFetchOptions, NitroFetchRequest } from 'nitropack'
import { $api } from '../composables/useApiFetch'

/**
 * Interface pour les options de requête étendant les types natifs de Nitro ($fetch)
 */
interface ApiRequestOptions<ResT, TransformT> extends Omit<
  NitroFetchOptions<NitroFetchRequest>,
  'transform'
> {
  transform?: (data: ResT) => TransformT
}

export abstract class BaseRepository {
  /**
   * apiRequest utilise désormais $api ($fetch).
   * Suppression du try/catch inutile car l'erreur est re-jetée sans traitement.
   */
  protected async apiRequest<ResT, TransformT = ResT>(
    url: string,
    options: ApiRequestOptions<ResT, TransformT> = {},
  ): Promise<{ data: TransformT }> {
    const response = await $api<ResT>(url, options)

    // On applique manuellement le transform si fourni, sinon on cast
    // Utilisation de unknown avant le cast final pour la sécurité TS
    const data = options.transform
      ? options.transform(response)
      : (response as unknown as TransformT)

    return { data }
  }
}
