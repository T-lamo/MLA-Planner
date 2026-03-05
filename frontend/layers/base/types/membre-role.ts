import type { UUID } from './shared'

/**
 * Type littéral pour les niveaux de compétence.
 * Aligné sur la validation Pydantic du Backend.
 */
export type NiveauCompetence = 'DEBUTANT' | 'INTERMEDIAIRE' | 'AVANCE' | 'EXPERT'

/**
 * BASE
 */
export interface MembreRoleBase {
  membre_id: UUID
  role_code: string
  niveau: NiveauCompetence
  is_principal: boolean
}

/**
 * CREATE
 * Identique à la base car tous les champs sont requis pour la clé composite.
 */
export type MembreRoleCreate = MembreRoleBase

/**
 * UPDATE
 * Seuls le niveau et le statut principal sont modifiables
 * (la clé composite membre_id/role_code ne change pas).
 */
export interface MembreRoleUpdate {
  niveau?: NiveauCompetence
  is_principal?: boolean
}

/**
 * READ
 */
export type MembreRoleRead = MembreRoleBase
