import type { UUID, PaginatedResponse } from './shared'
import type { ProfilReadFull } from './profiles'
import type { MinistereSimple } from './ministere'

export interface CampusBase {
  nom: string
  ville: string
  timezone: string
}

export interface CampusCreate extends CampusBase {
  pays_id: UUID
}

export type CampusUpdate = Partial<CampusCreate>

export interface CampusRead extends CampusBase {
  id: UUID
  pays_id: UUID
}

export interface CampusReadWithDetails extends CampusRead {
  membres: ProfilReadFull[]
  ministeres: MinistereSimple[]
}

export type CampusPaginationResponse = PaginatedResponse<CampusRead>
