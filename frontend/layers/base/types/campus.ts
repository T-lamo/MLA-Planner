import type { UUID, PaginatedResponse } from './shared'
import type { ProfilReadFull } from './profiles'
import type { MinistereSimple } from './ministere'

export interface CampusBase {
  nom: string
  ville: string
  pays?: string | null
  timezone: string
}

export interface CampusCreate extends CampusBase {
  organisation_id: UUID
}

export type CampusUpdate = Partial<Omit<CampusCreate, 'organisation_id'>> & {
  organisation_id?: UUID
}

export interface CampusRead extends CampusBase {
  id: UUID
  organisation_id: UUID
}

export interface CampusReadWithDetails extends CampusRead {
  membres: ProfilReadFull[]
  ministeres: MinistereSimple[]
}

export type CampusPaginationResponse = PaginatedResponse<CampusRead>
