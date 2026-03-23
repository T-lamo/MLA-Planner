import type { UUID } from './shared'
import type { MembreSimple } from './membre'

/**
 * BASE
 * Propriétés communes aux pôles.
 */
export interface PoleBase {
  nom: string
  description?: string // Optional en Python
  active: boolean
}

/**
 * CREATE
 * Schéma pour la création d'un pôle.
 */
export interface PoleCreate extends PoleBase {
  ministere_id: UUID
}

/**
 * READ
 * Version allégée utilisée pour l'inclusion dans d'autres objets (Ministère, Profil).
 * Évite les récursions infinies en excluant la liste complète des membres.
 */
export interface PoleSimple extends PoleBase {
  id: UUID
  ministere_id: UUID
  membres_count: number
}

/**
 * READ WITH RELATIONS
 * Version riche pour l'affichage détaillé d'un pôle spécifique.
 */
export interface PoleSimpleWithMembres extends PoleSimple {
  /**
   * Alias 'membres' provenant du champ Python 'poles_membres'
   */
  membres: MembreSimple[]
}

/**
 * UPDATE
 * Version pour la mise à jour partielle.
 */
export interface PoleUpdate extends Partial<PoleBase> {
  ministere_id?: UUID
}
