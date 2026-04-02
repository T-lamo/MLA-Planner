import type { PaginatedResponse } from '../../types/api'
import type { CampusRead } from '../../types/campus'
import type { MinistereSimple } from '../../types/ministere'
import type {
  ProfilCreateFull,
  ProfilReadFull,
  ProfilSelfUpdate,
  ProfilUpdateFull,
} from '../../types/profiles'
import { GenericRepository } from './GeneriqueRepository'
export class ProfileRepository extends GenericRepository<
  ProfilReadFull,
  ProfilCreateFull,
  ProfilUpdateFull,
  PaginatedResponse<ProfilReadFull>
> {
  constructor() {
    super('/profiles')
  }

  /**
   * Récupère tous les profils d'un campus spécifique
   */
  async getMyProfile(): Promise<ProfilReadFull> {
    const { data } = await this.apiRequest<ProfilReadFull>('/profiles/me')
    return data
  }

  async changePassword(
    userId: string,
    currentPassword: string,
    newPassword: string,
  ): Promise<void> {
    await this.apiRequest(`/auth/utilisateurs/${userId}/password`, {
      method: 'PATCH',
      body: { current_password: currentPassword, new_password: newPassword },
    })
  }

  async updateMyProfile(payload: ProfilSelfUpdate): Promise<ProfilReadFull> {
    const { data } = await this.apiRequest<ProfilReadFull>('/profiles/me', {
      method: 'PATCH',
      body: payload,
    })
    return data
  }

  async getMyCampuses(): Promise<CampusRead[]> {
    const { data } = await this.apiRequest<CampusRead[]>('/profiles/me/campuses')
    return data
  }

  async getAllCampuses(): Promise<CampusRead[]> {
    const { data } = await this.apiRequest<{ data: CampusRead[] }>('/campuses/all')
    return (data as unknown as { data: CampusRead[] }).data
  }

  async getAllByCampus(
    campusId: string,
    params?: Record<string, unknown>,
  ): Promise<PaginatedResponse<ProfilReadFull>> {
    const { data } = await this.apiRequest<PaginatedResponse<ProfilReadFull>>(
      `${this.endpoint}/campus/${campusId}`,
      {
        method: 'GET',
        query: params,
      },
    )
    return data
  }

  async getAllByCampusFull(campusId: string): Promise<ProfilReadFull[]> {
    const { data } = await this.apiRequest<{ data: ProfilReadFull[] }>(
      `${this.endpoint}/campus/${campusId}/all`,
    )
    return (data as unknown as { data: ProfilReadFull[] }).data
  }

  async getAllByMinistere(ministereId: string, campusId?: string): Promise<ProfilReadFull[]> {
    const { data } = await this.apiRequest<{ data: ProfilReadFull[] }>(
      `${this.endpoint}/ministere/${ministereId}`,
      { query: campusId ? { campus_id: campusId } : undefined },
    )
    return (data as unknown as { data: ProfilReadFull[] }).data
  }

  async getMyMinisteresByCampus(campusId: string): Promise<MinistereSimple[]> {
    const { data } = await this.apiRequest<MinistereSimple[]>(
      `/profiles/me/ministeres/by-campus/${campusId}`,
    )
    return data
  }
}
