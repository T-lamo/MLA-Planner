import type { UUID, ISO8601String, PaginatedResponse } from './shared'
import type { MembreSimple } from './membre' // Import nécessaire selon Python
import type { PoleSimple } from './pole' // Import nécessaire selon Python

/**
 * BASE
 * Structure commune à la plupart des modèles Ministère.
 */
export interface MinistereBase {
  nom: string
  date_creation: ISO8601String
  actif: boolean
}

/**
 * MINISTERE SIMPLE
 * Version ultra-légère pour les références rapides (sélecteurs, listes profils).
 */
export interface MinistereSimple {
  id: UUID
  nom: string
  actif: boolean
}

/**
 * CREATE
 * Schéma pour l'envoi de données lors de la création.
 */
export interface MinistereCreate extends MinistereBase {
  campus_ids: UUID[]
}

/**
 * READ
 * Version optimisée utilisée pour l'inclusion dans d'autres objets (ex: ProfilReadFull).
 */
export interface MinistereRead extends MinistereBase {
  id: UUID
  // Note: Python mentionne que PoleSimple est inclus car "petit"
}

/**
 * READ WITH RELATIONS
 * Version riche utilisée pour l'administration et les vues détaillées.
 */
export interface MinistereReadWithRelations extends MinistereRead {
  /** * Alias 'membres' provenant du champ Python 'ministeres_membres'
   */
  membres: MembreSimple[]

  /**
   * Relations Pôles
   */
  poles: PoleSimple[]

  /**
   * Champs calculés (@computed_field)
   */
  membres_count: number
  poles_count: number
}

/**
 * UPDATE
 * Version pour la mise à jour partielle.
 * Utilise Partial<T> sur les champs scalaires et redéfinit les relations.
 */
export interface MinistereUpdate extends Partial<MinistereBase> {
  campus_ids?: UUID[]
}

export type MinisterePaginationResponse = PaginatedResponse<MinistereRead>
