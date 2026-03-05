import type { PaginatedResponse } from '../../types/api'
import type { ProfilCreateFull, ProfilReadFull, ProfilUpdateFull } from '../../types/profiles'
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
}
