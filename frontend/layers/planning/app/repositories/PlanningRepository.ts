import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'
import type {
  CampusFilterParams,
  PlanningFullCreate,
  PlanningFullRead,
  PlanningFullUpdate,
} from '../types/planning.types'

export class PlanningRepository extends BaseRepository {
  private readonly endpoint = '/plannings'

  /**
   * Extrait le contenu de l'enveloppe `{ data: T }` retournée par le backend.
   * Les endpoints custom (full, by-ministere, etc.) utilisent DataResponse/DataListResponse.
   */
  private async unwrap<T>(
    url: string,
    options?: Parameters<BaseRepository['apiRequest']>[1],
  ): Promise<T> {
    const { data } = await this.apiRequest<{ data: T }>(url, options)
    return (data as unknown as { data: T }).data
  }

  // -----------------------------------------------------------------------
  // Lecture
  // -----------------------------------------------------------------------

  async getFullPlanning(id: string): Promise<PlanningFullRead> {
    return this.unwrap<PlanningFullRead>(`${this.endpoint}/${id}/full`)
  }

  async listByMinistere(ministereId: string): Promise<PlanningFullRead[]> {
    return this.unwrap<PlanningFullRead[]>(`${this.endpoint}/by-ministere/${ministereId}`)
  }

  /**
   * Plannings de l'utilisateur connecté (slots où il est affecté).
   * Endpoint : GET /plannings/my/calendar — implémenté dans MLA-PLAN-07.
   */
  async listMyCalendar(): Promise<PlanningFullRead[]> {
    return this.unwrap<PlanningFullRead[]>(`${this.endpoint}/my/calendar`)
  }

  /**
   * Tous les plannings d'un campus, avec filtres optionnels.
   * Endpoint : GET /plannings/by-campus/{campus_id} — implémenté dans MLA-PLAN-07.
   */
  async listByCampus(campusId: string, filters?: CampusFilterParams): Promise<PlanningFullRead[]> {
    return this.unwrap<PlanningFullRead[]>(`${this.endpoint}/by-campus/${campusId}`, {
      query: filters as Record<string, unknown>,
    })
  }

  // -----------------------------------------------------------------------
  // Création / Modification / Suppression
  // -----------------------------------------------------------------------

  async createFull(payload: PlanningFullCreate): Promise<PlanningFullRead> {
    const { data } = await this.apiRequest<PlanningFullRead>(`${this.endpoint}/full`, {
      method: 'POST',
      body: payload,
    })
    return data
  }

  async updateFull(id: string, payload: PlanningFullUpdate): Promise<PlanningFullRead> {
    const { data } = await this.apiRequest<PlanningFullRead>(`${this.endpoint}/${id}/full`, {
      method: 'PATCH',
      body: payload,
    })
    return data
  }

  /**
   * Avance le workflow du planning.
   * new_status est un query param (type simple, non-Pydantic côté FastAPI).
   */
  async updateStatus(id: string, newStatus: string): Promise<void> {
    await this.apiRequest(`${this.endpoint}/${id}/status`, {
      method: 'PATCH',
      query: { new_status: newStatus },
    })
  }

  async deleteFull(id: string): Promise<void> {
    await this.apiRequest(`${this.endpoint}/${id}/full`, {
      method: 'DELETE',
    })
  }
}
