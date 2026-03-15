import { BaseRepository } from './BaseRepository'
import type {
  CampusConfigSummary,
  CampusSetupPayload,
  CampusSetupResult,
  CategorieConfigCreate,
  CategorieConfigResponse,
  CategorieConfigUpdate,
  CategorieRoleRead,
  MinistereConfigCreate,
  MinistereConfigResponse,
  MinistereConfigUpdate,
  MinistereRead,
  RbacRolesInitResponse,
  RoleCompetenceConfigApiResponse,
  RoleCompetenceConfigCreate,
  RoleCompetenceConfigUpdate,
  StatutsInitResponse,
} from '~~/layers/base/types/campus-config'
import type { CampusRead } from '~~/layers/base/types/campus'

export class CampusConfigRepository extends BaseRepository {
  async listCampuses(): Promise<CampusRead[]> {
    const { data } = await this.apiRequest<CampusRead[]>('/config/campus')
    return data
  }

  async getCampusSummary(campusId: string): Promise<CampusConfigSummary> {
    const { data } = await this.apiRequest<CampusConfigSummary>(
      `/config/campus/${campusId}/summary`,
    )
    return data
  }

  async addMinistere(
    campusId: string,
    payload: MinistereConfigCreate,
  ): Promise<MinistereConfigResponse> {
    const { data } = await this.apiRequest<MinistereConfigResponse>(
      `/config/campus/${campusId}/ministeres`,
      { method: 'POST', body: payload },
    )
    return data
  }

  async removeMinistere(campusId: string, ministereId: string): Promise<void> {
    await this.apiRequest<undefined>(`/config/campus/${campusId}/ministeres/${ministereId}`, {
      method: 'DELETE',
    })
  }

  async listMinisteres(campusId: string): Promise<MinistereRead[]> {
    const { data } = await this.apiRequest<MinistereRead[]>(`/config/campus/${campusId}/ministeres`)
    return data
  }

  async addCategorie(
    ministereId: string,
    payload: CategorieConfigCreate,
  ): Promise<CategorieConfigResponse> {
    const { data } = await this.apiRequest<CategorieConfigResponse>(
      `/config/ministeres/${ministereId}/categories`,
      { method: 'POST', body: payload },
    )
    return data
  }

  async deleteCategorie(ministereId: string, categorieId: string): Promise<void> {
    await this.apiRequest<undefined>(
      `/config/ministeres/${ministereId}/categories/${categorieId}`,
      {
        method: 'DELETE',
      },
    )
  }

  async listCategories(ministereId: string): Promise<CategorieRoleRead[]> {
    const { data } = await this.apiRequest<CategorieRoleRead[]>(
      `/config/ministeres/${ministereId}/categories`,
    )
    return data
  }

  async addRoleCompetence(
    categorieId: string,
    payload: RoleCompetenceConfigCreate,
  ): Promise<RoleCompetenceConfigApiResponse> {
    const { data } = await this.apiRequest<RoleCompetenceConfigApiResponse>(
      `/config/categories/${categorieId}/roles-competence`,
      { method: 'POST', body: payload },
    )
    return data
  }

  async deleteRoleCompetence(categorieId: string, roleCode: string): Promise<void> {
    await this.apiRequest<undefined>(
      `/config/categories/${categorieId}/roles-competence/${roleCode}`,
      {
        method: 'DELETE',
      },
    )
  }

  async linkRoleCompetence(categorieId: string, roleCode: string): Promise<void> {
    await this.apiRequest<RoleCompetenceConfigApiResponse>(
      `/config/categories/${categorieId}/roles-competence/${encodeURIComponent(roleCode)}/link`,
      { method: 'POST' },
    )
  }

  async updateMinistere(
    ministereId: string,
    payload: MinistereConfigUpdate,
  ): Promise<MinistereRead> {
    const { data } = await this.apiRequest<MinistereRead>(`/config/ministeres/${ministereId}`, {
      method: 'PATCH',
      body: payload,
    })
    return data
  }

  async updateCategorie(
    ministereId: string,
    categorieId: string,
    payload: CategorieConfigUpdate,
  ): Promise<CategorieRoleRead> {
    const { data } = await this.apiRequest<CategorieRoleRead>(
      `/config/ministeres/${ministereId}/categories/${categorieId}`,
      { method: 'PATCH', body: payload },
    )
    return data
  }

  async updateRoleCompetence(
    categorieId: string,
    roleCode: string,
    payload: RoleCompetenceConfigUpdate,
  ): Promise<void> {
    await this.apiRequest<unknown>(
      `/config/categories/${categorieId}/roles-competence/${encodeURIComponent(roleCode)}`,
      { method: 'PATCH', body: payload },
    )
  }

  async initRbacRoles(campusId: string, ministereId: string): Promise<RbacRolesInitResponse> {
    const { data } = await this.apiRequest<RbacRolesInitResponse>(
      `/config/campus/${campusId}/ministeres/${ministereId}/rbac-roles/init`,
      { method: 'POST' },
    )
    return data
  }

  async initStatuts(): Promise<StatutsInitResponse> {
    const { data } = await this.apiRequest<StatutsInitResponse>('/config/statuts/init', {
      method: 'POST',
    })
    return data
  }

  async setupCampus(campusId: string, payload: CampusSetupPayload): Promise<CampusSetupResult> {
    const { data } = await this.apiRequest<CampusSetupResult>(`/config/campus/${campusId}/setup`, {
      method: 'POST',
      body: payload,
    })
    return data
  }
}
