import { BaseRepository } from './BaseRepository'

/**
 * T : Entité de lecture (ex: ProfilReadFull)
 * TC : Schéma de création (ex: ProfilCreateFull)
 * TU : Schéma de mise à jour (ex: ProfilUpdateFull)
 * TR : Réponse paginée (ex: ProfilesPaginationResponse)
 */
export abstract class GenericRepository<
  T,
  TC extends object,
  TU extends object,
  TR,
> extends BaseRepository {
  /**
   * @param endpoint - Chemin de base de l'API (ex: '/profiles')
   */
  protected constructor(protected readonly endpoint: string) {
    super()
  }

  /**
   * Récupère la liste paginée avec des paramètres de requête
   */
  async getAll(params?: Record<string, unknown>): Promise<TR> {
    const { data } = await this.apiRequest<TR>(`${this.endpoint}/`, {
      method: 'GET',
      query: params,
    })
    return data
  }

  /**
   * Récupère une entité par son ID
   */
  async getById(id: string): Promise<T> {
    const { data } = await this.apiRequest<T>(`${this.endpoint}/${id}`)
    return data
  }

  /**
   * Crée une nouvelle ressource
   */
  async create(payload: TC): Promise<T> {
    const { data } = await this.apiRequest<T>(`${this.endpoint}/`, {
      method: 'POST',
      body: payload,
    })
    return data
  }

  /**
   * Mise à jour partielle (PATCH) d'une ressource
   */
  async update(id: string, payload: TU): Promise<T> {
    const { data } = await this.apiRequest<T>(`${this.endpoint}/${id}`, {
      method: 'PATCH',
      body: payload,
    })
    return data
  }

  /**
   * Supprime une ressource
   */
  async delete(id: string): Promise<void> {
    await this.apiRequest<undefined>(`${this.endpoint}/${id}`, {
      method: 'DELETE',
    })
  }
}
