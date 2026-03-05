import type {
  MinistereCreate,
  MinisterePaginationResponse,
  MinistereRead,
  MinistereReadWithRelations,
  MinistereUpdate,
} from '../../types/ministere'
import { GenericRepository } from './GeneriqueRepository'

export class MinistereRepository extends GenericRepository<
  MinistereRead,
  MinistereCreate,
  MinistereUpdate,
  MinisterePaginationResponse
> {
  constructor() {
    super('/ministeres')
  }

  /**
   * Récupère le détail complet avec relations.
   * On surcharge le comportement pour extraire la clé "data" de l'enveloppe API.
   */
  async getFullById(id: string): Promise<MinistereReadWithRelations> {
    const { data } = await this.apiRequest<{ data: MinistereReadWithRelations }>(
      `${this.endpoint}/${id}/full`,
    )
    // apiRequest renvoie déjà { data }, on extrait le contenu de l'enveloppe JSON
    return (data as unknown as { data: MinistereReadWithRelations }).data
  }

  /**
   * Surcharge optionnelle de getById si vous souhaitez
   * que l'appel standard gère aussi l'enveloppe.
   */
  override async getById(id: string): Promise<MinistereRead> {
    const { data } = await this.apiRequest<{ data: MinistereRead }>(`${this.endpoint}/${id}/`)
    return (data as unknown as { data: MinistereRead }).data
  }
}
