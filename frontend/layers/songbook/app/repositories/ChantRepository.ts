import { BaseRepository } from '~~/layers/base/app/repositories/BaseRepository'
import type {
  ChantCategorieCreate,
  ChantCategorieRead,
  ChantCategorieUpdate,
  ChantContenuCreate,
  ChantContenuRead,
  ChantContenuUpdate,
  ChantCreate,
  ChantListParams,
  ChantRead,
  ChantReadFull,
  ChantTransposeRequest,
  ChantTransposeResponse,
  ChantUpdate,
  PaginatedChants,
} from '../types/chant'

export class ChantRepository extends BaseRepository {
  // ---- Catégories ----

  async listCategories(): Promise<ChantCategorieRead[]> {
    const { data } = await this.apiRequest<ChantCategorieRead[]>('/chants/categories')
    return data
  }

  async createCategorie(payload: ChantCategorieCreate): Promise<ChantCategorieRead> {
    const { data } = await this.apiRequest<ChantCategorieRead>('/chants/categories', {
      method: 'POST',
      body: payload,
    })
    return data
  }

  async updateCategorie(code: string, payload: ChantCategorieUpdate): Promise<ChantCategorieRead> {
    const { data } = await this.apiRequest<ChantCategorieRead>(
      `/chants/categories/${encodeURIComponent(code)}`,
      { method: 'PATCH', body: payload },
    )
    return data
  }

  async deleteCategorie(code: string): Promise<void> {
    await this.apiRequest<undefined>(`/chants/categories/${encodeURIComponent(code)}`, {
      method: 'DELETE',
    })
  }

  // ---- Chants ----

  async listChants(params: ChantListParams): Promise<PaginatedChants> {
    const query = new URLSearchParams()
    if (params.campus_id) query.set('campus_id', params.campus_id)
    if (params.categorie_code) query.set('categorie_code', params.categorie_code)
    if (params.artiste) query.set('artiste', params.artiste)
    if (params.q) query.set('q', params.q)
    if (params.limit != null) query.set('limit', String(params.limit))
    if (params.offset != null) query.set('offset', String(params.offset))
    const { data } = await this.apiRequest<PaginatedChants>(`/chants?${query.toString()}`)
    return data
  }

  async getChant(id: string): Promise<ChantReadFull> {
    const { data } = await this.apiRequest<ChantReadFull>(`/chants/${id}`)
    return data
  }

  async createChant(payload: ChantCreate): Promise<ChantRead> {
    const { data } = await this.apiRequest<ChantRead>('/chants', {
      method: 'POST',
      body: payload,
    })
    return data
  }

  async updateChant(id: string, payload: ChantUpdate): Promise<ChantRead> {
    const { data } = await this.apiRequest<ChantRead>(`/chants/${id}`, {
      method: 'PATCH',
      body: payload,
    })
    return data
  }

  async deleteChant(id: string): Promise<void> {
    await this.apiRequest<undefined>(`/chants/${id}`, { method: 'DELETE' })
  }

  // ---- Contenu ChordPro ----

  async getContenu(chantId: string): Promise<ChantContenuRead> {
    const { data } = await this.apiRequest<ChantContenuRead>(`/chants/${chantId}/contenu`)
    return data
  }

  async upsertContenu(chantId: string, payload: ChantContenuCreate): Promise<ChantContenuRead> {
    const { data } = await this.apiRequest<ChantContenuRead>(`/chants/${chantId}/contenu`, {
      method: 'PUT',
      body: payload,
    })
    return data
  }

  async updateContenu(chantId: string, payload: ChantContenuUpdate): Promise<ChantContenuRead> {
    const { data } = await this.apiRequest<ChantContenuRead>(`/chants/${chantId}/contenu`, {
      method: 'PATCH',
      body: payload,
    })
    return data
  }

  async transpose(
    chantId: string,
    payload: ChantTransposeRequest,
  ): Promise<ChantTransposeResponse> {
    const { data } = await this.apiRequest<ChantTransposeResponse>(
      `/chants/${chantId}/contenu/transpose`,
      { method: 'POST', body: payload },
    )
    return data
  }
}
