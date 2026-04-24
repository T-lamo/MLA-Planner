import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'
import type { PaginatedResponse } from '~~/layers/base/types/shared'
import type { AffectationMemberRead, AffectationStatus } from '../types/planning.types'

export class AffectationRepository extends BaseRepository {
  async getMyAffectations(params: {
    limit: number
    offset: number
  }): Promise<PaginatedResponse<AffectationMemberRead>> {
    const { data } = await this.apiRequest<PaginatedResponse<AffectationMemberRead>>(
      '/affectations/me',
      { query: params },
    )
    return data
  }

  async getPendingCount(): Promise<number> {
    const { data } = await this.apiRequest<number>('/affectations/me/pending-count')
    return data as unknown as number
  }

  async updateMyStatus(affectationId: string, newStatus: AffectationStatus): Promise<void> {
    await this.apiRequest(`/affectations/${affectationId}/my-status`, {
      method: 'PATCH',
      query: { new_status: newStatus },
    })
  }

  async updateStatus(affectationId: string, newStatus: AffectationStatus): Promise<void> {
    await this.apiRequest(`/affectations/${affectationId}/status`, {
      method: 'PATCH',
      query: { new_status: newStatus },
    })
  }
}
