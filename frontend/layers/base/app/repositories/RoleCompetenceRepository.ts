import { GenericRepository } from './GeneriqueRepository'
import type {
  RoleCompetenceRead,
  RolesByCategoryItem,
  RolesByCategoryResponse,
} from '../../types/role-competence'

export class RoleCompetenceRepository extends GenericRepository<
  RoleCompetenceRead,
  never,
  never,
  RolesByCategoryResponse
> {
  constructor() {
    super('/roles-competences')
  }

  async getByCategory(ministereId?: string): Promise<RolesByCategoryItem[]> {
    const url = ministereId
      ? `${this.endpoint}/by-category/full?ministere_id=${encodeURIComponent(ministereId)}`
      : `${this.endpoint}/by-category/full`
    const { data } = await this.apiRequest<RolesByCategoryResponse>(url, { method: 'GET' })
    return data.data
  }
}
