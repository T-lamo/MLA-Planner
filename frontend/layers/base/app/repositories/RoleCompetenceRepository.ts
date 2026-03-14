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

  async getByCategory(): Promise<RolesByCategoryItem[]> {
    const { data } = await this.apiRequest<RolesByCategoryResponse>(
      `${this.endpoint}/by-category/full`,
      { method: 'GET' },
    )
    return data.data
  }
}
