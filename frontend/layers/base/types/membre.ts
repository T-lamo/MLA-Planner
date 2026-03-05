import type { UUID, ISO8601String } from './shared'
import type { UtilisateurRead } from './utilisateur'
import type { MembreRoleRead } from './membre-role'

// --- VERSIONS "SIMPLE" POUR LE CONTEXTE MEMBRE ---

/**
 * Vue utilisateur sans membre_id pour éviter la redondance dans le parent.
 */
export interface UtilisateurSimple extends Omit<UtilisateurRead, 'membre_id'> {
  membre_id?: null
}

/**
 * Vue rôle sans membre_id.
 */
export interface MembreRoleSimple extends Omit<MembreRoleRead, 'membre_id'> {
  membre_id?: null
}

// -------------------------
// BASE
// -------------------------
export interface MembreBase {
  nom: string
  prenom: string
  email?: string | null
  telephone?: string | null
  actif: boolean
}

// -------------------------
// MEMBRE SIMPLE
// -------------------------
/**
 * Version ultra-légère utilisée pour les listes imbriquées (Ministères/Pôles).
 */
export interface MembreSimple extends MembreBase {
  id: UUID
  date_inscription: ISO8601String
}

// -------------------------
// READ
// -------------------------
/**
 * Version standard pour la lecture d'un membre avec ses relations de base.
 */
export interface MembreRead extends MembreBase {
  id: UUID
  date_inscription: ISO8601String
  utilisateur: UtilisateurSimple | null
  roles_assoc: MembreRoleSimple[]
}

// -------------------------
// CREATE / UPDATE
// -------------------------
export interface MembreCreate extends MembreBase {
  campus_ids: UUID[]
  ministere_ids: UUID[]
  pole_ids: UUID[]
}

export interface MembreUpdate extends Partial<MembreBase> {
  campus_ids?: UUID[]
  ministere_ids?: UUID[]
  pole_ids?: UUID[]
}

// -------------------------
// RÉPONSES PAGINÉES
// -------------------------
export interface MembrePaginatedResponse {
  total: number
  limit: number
  offset: number
  data: MembreRead[]
}

// -------------------------
// SCHÉMAS D'AGENDA
// -------------------------

export interface MemberAgendaEntryRead {
  affectation_id: string
  statut_affectation_code: string
  role_code: string
  nom_creneau: string
  date_debut: ISO8601String
  date_fin: ISO8601String
  activite_nom: string
  activite_type: string
  lieu?: string | null
  campus_nom: string
}

export interface MemberAgendaStats {
  total_engagements: number
  confirmed_rate: number
  roles_distribution: Record<string, number>
}

export interface MemberAgendaResponse {
  period_start: ISO8601String
  period_end: ISO8601String
  statistics: MemberAgendaStats
  entries: MemberAgendaEntryRead[]
}
