import type {
  CampusCreate,
  CampusPaginationResponse,
  CampusRead,
  CampusUpdate,
} from '../../types/campus'
import type { MinistereReadWithRelations } from '../../types/ministere'
import { GenericRepository } from './GeneriqueRepository'

export class CampusRepository extends GenericRepository<
  CampusRead,
  CampusCreate,
  CampusUpdate,
  CampusPaginationResponse
> {
  constructor() {
    super('/campuses')
  }
  /**
   * Récupère la liste enrichie des ministères pour un campus donné.
   * Typage strict basé sur MinistereReadWithRelations[].
   */
  async getDetailedMinisteres(campusId: string): Promise<MinistereReadWithRelations[]> {
    // apiRequest retourne déjà { data: T }
    const { data } = await this.apiRequest<MinistereReadWithRelations[]>(
      `${this.endpoint}/${campusId}/ministeres/detailed`,
    )
    return (data as unknown as { data: MinistereReadWithRelations[] }).data
  }
}
