import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'
import type { MinistereSimple } from '~~/layers/base/types/ministere'
import type {
  CampusFilterParams,
  CampusTeamRead,
  MembreSimple,
  PlanningFullCreate,
  PlanningFullRead,
  PlanningFullUpdate,
  RoleCompetenceRead,
} from '../types/planning.types'

export class PlanningRepository extends BaseRepository {
  private readonly endpoint = '/plannings'

  /**
   * Extrait le contenu de l'enveloppe `{ data: T }` retournée par le backend.
   */
  private async unwrap<T>(
    url: string,
    options?: Omit<Parameters<BaseRepository['apiRequest']>[1], 'transform'>,
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

  async listByMinistere(ministereId: string, campusId?: string): Promise<PlanningFullRead[]> {
    return this.unwrap<PlanningFullRead[]>(`${this.endpoint}/by-ministere/${ministereId}`, {
      query: campusId ? { campus_id: campusId } : undefined,
    })
  }

  async listMyCalendar(campusId?: string): Promise<PlanningFullRead[]> {
    return this.unwrap<PlanningFullRead[]>(`${this.endpoint}/my/calendar`, {
      query: campusId ? { campus_id: campusId } : undefined,
    })
  }

  async listByCampus(campusId: string, filters?: CampusFilterParams): Promise<PlanningFullRead[]> {
    return this.unwrap<PlanningFullRead[]>(`${this.endpoint}/by-campus/${campusId}`, {
      query: filters as Record<string, unknown>,
    })
  }

  // -----------------------------------------------------------------------
  // Création / Modification / Suppression
  // -----------------------------------------------------------------------

  async createFull(payload: PlanningFullCreate): Promise<PlanningFullRead> {
    return this.unwrap<PlanningFullRead>(`${this.endpoint}/full`, {
      method: 'POST',
      body: payload,
    })
  }

  async updateFull(id: string, payload: PlanningFullUpdate): Promise<PlanningFullRead> {
    return this.unwrap<PlanningFullRead>(`${this.endpoint}/${id}/full`, {
      method: 'PATCH',
      body: payload,
    })
  }

  async updateStatus(id: string, newStatus: string): Promise<PlanningFullRead> {
    return this.unwrap<PlanningFullRead>(`${this.endpoint}/${id}/status`, {
      method: 'PATCH',
      query: { new_status: newStatus },
    })
  }

  async deleteFull(id: string): Promise<void> {
    await this.apiRequest(`${this.endpoint}/${id}/full`, {
      method: 'DELETE',
    })
  }

  // -----------------------------------------------------------------------
  // Données de référence pour le formulaire
  // -----------------------------------------------------------------------

  async getMembersByMinistere(ministereId: string): Promise<MembreSimple[]> {
    const { data } = await this.apiRequest<MembreSimple[]>(`/membres/by-ministere/${ministereId}`)
    return data
  }

  async getRoleCompetences(): Promise<RoleCompetenceRead[]> {
    return this.unwrap<RoleCompetenceRead[]>('/roles-competences/all')
  }

  async getMyMinistreresByCampus(campusId: string): Promise<MinistereSimple[]> {
    const { data } = await this.apiRequest<MinistereSimple[]>(
      `/profiles/me/ministeres/by-campus/${campusId}`,
    )
    return data
  }

  async getCampusTeam(campusId: string): Promise<CampusTeamRead> {
    const { data } = await this.apiRequest<CampusTeamRead>(`/campus/${campusId}/team`)
    return data
  }
}
