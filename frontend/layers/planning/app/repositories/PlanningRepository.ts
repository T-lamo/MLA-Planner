import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'
import type { PaginatedResponse } from '~~/layers/base/types/shared'
import type { MinistereSimple } from '~~/layers/base/types/ministere'
import type {
  ApplyTemplateResult,
  CampusFilterParams,
  CampusTeamRead,
  GenerateSeriesForm,
  GenerateSeriesResponse,
  MembreSimple,
  PlanningChantRead,
  PlanningFullCreate,
  PlanningFullRead,
  PlanningFullUpdate,
  PlanningRepertoireUpdate,
  PlanningTemplateFullUpdate,
  PlanningTemplateListItem,
  PlanningTemplateRead,
  PlanningTemplateReadFull,
  RoleCompetenceRead,
  SaveAsTemplateRequest,
  SeriesPreviewResponse,
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

  // -----------------------------------------------------------------------
  // Planning Templates — US-01
  // -----------------------------------------------------------------------

  async saveAsTemplate(
    planningId: string,
    payload: SaveAsTemplateRequest,
  ): Promise<PlanningTemplateRead> {
    return this.unwrap<PlanningTemplateRead>(`/planning-templates/from-planning/${planningId}`, {
      method: 'POST',
      body: payload,
    })
  }

  async listTemplatesByCampus(campusId: string): Promise<PlanningTemplateRead[]> {
    return this.unwrap<PlanningTemplateRead[]>(`/planning-templates/by-campus/${campusId}`)
  }

  async listTemplatesByMinistere(ministereId: string): Promise<PlanningTemplateRead[]> {
    return this.unwrap<PlanningTemplateRead[]>(`/planning-templates/by-ministere/${ministereId}`)
  }

  async deleteTemplate(templateId: string): Promise<void> {
    await this.apiRequest(`/planning-templates/${templateId}`, {
      method: 'DELETE',
    })
  }

  // ── US-95 : bibliothèque de templates ───────────────────────────────────

  async listTemplates(
    ministereId?: string,
    params?: { limit: number; offset: number },
  ): Promise<PaginatedResponse<PlanningTemplateListItem>> {
    const { data } = await this.apiRequest<PaginatedResponse<PlanningTemplateListItem>>(
      '/planning-templates',
      { query: { ...(ministereId ? { ministere_id: ministereId } : {}), ...params } },
    )
    return data
  }

  async getTemplateFull(id: string): Promise<PlanningTemplateReadFull> {
    return this.unwrap<PlanningTemplateReadFull>(`/planning-templates/${id}`)
  }

  async updateTemplateFull(
    id: string,
    payload: PlanningTemplateFullUpdate,
  ): Promise<PlanningTemplateReadFull> {
    return this.unwrap<PlanningTemplateReadFull>(`/planning-templates/${id}`, {
      method: 'PUT',
      body: payload,
    })
  }

  async duplicateTemplate(id: string): Promise<PlanningTemplateListItem> {
    return this.unwrap<PlanningTemplateListItem>(`/planning-templates/${id}/duplicate`, {
      method: 'POST',
    })
  }

  // ── US-96 : application d'un template sur un planning ───────────────────

  async applyTemplate(templateId: string, planningId: string): Promise<ApplyTemplateResult> {
    return this.unwrap<ApplyTemplateResult>(
      `/planning-templates/${templateId}/apply/${planningId}`,
      { method: 'POST' },
    )
  }

  // ── US-98 : génération de séries ─────────────────────────────────────────

  async previewSeries(form: GenerateSeriesForm): Promise<SeriesPreviewResponse> {
    const { data } = await this.apiRequest<SeriesPreviewResponse>(
      '/planning-templates/preview-series',
      { method: 'POST', body: form },
    )
    return data
  }

  async generateSeries(
    templateId: string,
    form: GenerateSeriesForm,
  ): Promise<GenerateSeriesResponse> {
    const { data } = await this.apiRequest<GenerateSeriesResponse>(
      '/planning-templates/generate-series',
      { method: 'POST', body: { ...form, template_id: templateId } },
    )
    return data
  }

  // ── Répertoire de chants ──────────────────────────────────────────────────

  async getRepertoire(planningId: string): Promise<PlanningChantRead[]> {
    return this.unwrap<PlanningChantRead[]>(`${this.endpoint}/${planningId}/repertoire`)
  }

  async setRepertoire(
    planningId: string,
    payload: PlanningRepertoireUpdate,
  ): Promise<PlanningChantRead[]> {
    return this.unwrap<PlanningChantRead[]>(`${this.endpoint}/${planningId}/repertoire`, {
      method: 'PUT',
      body: payload,
    })
  }
}
