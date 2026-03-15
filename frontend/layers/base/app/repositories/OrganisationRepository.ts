import type { PaginatedResponse } from '../../types/shared'
import type {
  OrganisationCreate,
  OrganisationRead,
  OrganisationUpdate,
} from '../../types/organisation'
import { GenericRepository } from './GeneriqueRepository'

export class OrganisationRepository extends GenericRepository<
  OrganisationRead,
  OrganisationCreate,
  OrganisationUpdate,
  PaginatedResponse<OrganisationRead>
> {
  constructor() {
    super('/organisations')
  }

  /**
   * Récupère toutes les organisations sans pagination.
   */
  async getAllOrganisations(): Promise<OrganisationRead[]> {
    const { data } = await this.apiRequest<{ data: OrganisationRead[] }>('/organisations/all')
    return (data as unknown as { data: OrganisationRead[] }).data
  }
}
