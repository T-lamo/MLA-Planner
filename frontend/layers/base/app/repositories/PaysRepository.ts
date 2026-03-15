import type { PaginatedResponse } from '../../types/shared'
import type { PaysCreate, PaysRead, PaysUpdate } from '../../types/pays'
import { GenericRepository } from './GeneriqueRepository'

export class PaysRepository extends GenericRepository<
  PaysRead,
  PaysCreate,
  PaysUpdate,
  PaginatedResponse<PaysRead>
> {
  constructor() {
    super('/pays')
  }

  async getAllPays(): Promise<PaysRead[]> {
    const { data } = await this.apiRequest<{ data: PaysRead[] }>('/pays/all')
    return (data as unknown as { data: PaysRead[] }).data
  }
}
