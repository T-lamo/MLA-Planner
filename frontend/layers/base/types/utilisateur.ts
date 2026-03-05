import type { UUID } from './shared'

export interface UtilisateurBase {
  username: string
  actif: boolean
}

export interface UtilisateurRead extends UtilisateurBase {
  id: UUID
  membre_id: UUID
  roles: string[]
}

export interface UtilisateurWrite extends UtilisateurBase {
  password?: string
  roles_ids: UUID[]
}
