import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'
import type { AffectationMemberRead, AffectationStatus } from '../types/planning.types'

export class AffectationRepository extends BaseRepository {
  async getMyAffectations(): Promise<AffectationMemberRead[]> {
    const { data } = await this.apiRequest<AffectationMemberRead[]>('/affectations/me')
    return data as unknown as AffectationMemberRead[]
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
