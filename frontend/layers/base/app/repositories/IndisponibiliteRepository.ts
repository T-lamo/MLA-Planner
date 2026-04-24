// repositories/IndisponibiliteRepository.ts
import { BaseRepository } from './BaseRepository'
import type { PaginatedResponse } from '../../types/shared'
import type {
  IndisponibiliteCreate,
  IndisponibiliteFilters,
  IndisponibiliteRead,
  IndisponibiliteReadFull,
} from '../../types/indisponibilites'

export class IndisponibiliteRepository extends BaseRepository {
  async getMyIndisponibilites(params: {
    limit: number
    offset: number
  }): Promise<PaginatedResponse<IndisponibiliteReadFull>> {
    const { data } = await this.apiRequest<PaginatedResponse<IndisponibiliteReadFull>>(
      '/indisponibilites/me',
      { query: params },
    )
    return data
  }

  async create(payload: IndisponibiliteCreate): Promise<IndisponibiliteRead> {
    const { data } = await this.apiRequest<IndisponibiliteRead>('/indisponibilites/', {
      method: 'POST',
      body: payload,
    })
    return data
  }

  async delete(id: string): Promise<void> {
    await this.apiRequest(`/indisponibilites/${id}`, { method: 'DELETE' })
  }

  async getByCampus(
    campusId: string,
    filters?: IndisponibiliteFilters,
    params?: { limit: number; offset: number },
  ): Promise<PaginatedResponse<IndisponibiliteReadFull>> {
    const { data } = await this.apiRequest<PaginatedResponse<IndisponibiliteReadFull>>(
      `/indisponibilites/campus/${campusId}`,
      { query: { ...filters, ...params } },
    )
    return data
  }

  async valider(id: string): Promise<IndisponibiliteReadFull> {
    const { data } = await this.apiRequest<IndisponibiliteReadFull>(
      `/indisponibilites/${id}/valider`,
      { method: 'PATCH' },
    )
    return data
  }

  async adminDelete(id: string): Promise<void> {
    await this.apiRequest(`/indisponibilites/${id}/admin`, {
      method: 'DELETE',
    })
  }

  async getValidatedForPeriod(
    campusId: string,
    dateDebut: string,
    dateFin: string,
  ): Promise<IndisponibiliteReadFull[]> {
    const { data } = await this.apiRequest<IndisponibiliteReadFull[]>(
      `/indisponibilites/campus/${campusId}/period`,
      { query: { date_debut: dateDebut, date_fin: dateFin } },
    )
    return data
  }
}
