import type { UUID, ISO8601String, RoleNiveau, PaginatedResponse } from './shared'
import type { CampusRead } from './campus'
import type { MinistereSimple } from './ministere'
import type { PoleSimple } from './pole'
import type { UtilisateurRead, UtilisateurWrite } from './utilisateur'

export interface RoleAssoc {
  membre_id: UUID
  role_code: string
  niveau: RoleNiveau
  is_principal: boolean
}

export interface ProfilReadFull {
  id: UUID
  nom: string
  prenom: string
  email: string
  telephone: string | null
  actif: boolean
  date_inscription: ISO8601String
  utilisateur: UtilisateurRead | null
  roles_assoc: RoleAssoc[]
  campuses: CampusRead[]
  ministeres: MinistereSimple[]
  poles: PoleSimple[]
}

export interface ProfilCreateFull {
  nom: string
  prenom: string
  email: string
  telephone?: string | null
  actif: boolean
  campus_ids: UUID[]
  ministere_ids: UUID[]
  pole_ids: UUID[]
  utilisateur?: UtilisateurWrite
}

export interface ProfilUpdateFull extends Partial<Omit<ProfilCreateFull, 'utilisateur'>> {
  utilisateur?: Partial<UtilisateurWrite>
}

export type ProfilesPaginationResponse = PaginatedResponse<ProfilReadFull>
