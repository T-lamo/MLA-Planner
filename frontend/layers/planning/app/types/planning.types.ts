import type { EventInput } from '@fullcalendar/core'

// ============================================================
// 1. COULEURS — Palette déterministe par ministère
// ============================================================

export interface MinistereColor {
  bg: string
  text: string
  light: string
  border: string
}

/**
 * 10 couleurs distinctes, contraste WCAG AA garanti (texte blanc sur fond `bg`).
 * L'index est attribué selon la position du ministère dans la liste ordonnée
 * de l'utilisateur, garantissant la cohérence entre perspectives et sessions.
 */
export const MINISTERE_PALETTE: readonly MinistereColor[] = [
  { bg: '#3B82F6', text: '#FFFFFF', light: '#EFF6FF', border: '#93C5FD' }, // bleu
  { bg: '#10B981', text: '#FFFFFF', light: '#ECFDF5', border: '#6EE7B7' }, // vert
  { bg: '#F59E0B', text: '#FFFFFF', light: '#FFFBEB', border: '#FCD34D' }, // ambre
  { bg: '#8B5CF6', text: '#FFFFFF', light: '#F5F3FF', border: '#C4B5FD' }, // violet
  { bg: '#EF4444', text: '#FFFFFF', light: '#FEF2F2', border: '#FCA5A5' }, // rouge
  { bg: '#06B6D4', text: '#FFFFFF', light: '#ECFEFF', border: '#67E8F9' }, // cyan
  { bg: '#F97316', text: '#FFFFFF', light: '#FFF7ED', border: '#FDBA74' }, // orange
  { bg: '#EC4899', text: '#FFFFFF', light: '#FDF2F8', border: '#F9A8D4' }, // rose
  { bg: '#14B8A6', text: '#FFFFFF', light: '#F0FDFA', border: '#5EEAD4' }, // teal
  { bg: '#6366F1', text: '#FFFFFF', light: '#EEF2FF', border: '#A5B4FC' }, // indigo
] as const

/**
 * Retourne la couleur associée à un ministère de façon déterministe.
 * Si le ministère n'est pas dans la liste, retourne la première couleur.
 */
export function getMinistereColor(ministereId: string, allMinistereIds: string[]): MinistereColor {
  const idx = allMinistereIds.indexOf(ministereId)
  return MINISTERE_PALETTE[(idx >= 0 ? idx : 0) % MINISTERE_PALETTE.length]!
}

// ============================================================
// 2. STATUTS & PERSPECTIVES
// ============================================================

/** Correspond aux valeurs de l'enum PlanningStatusCode côté backend */
export type PlanningStatus = 'BROUILLON' | 'PUBLIE' | 'ANNULE' | 'TERMINE'

export type PlanningViewPerspective = 'PERSONAL' | 'MINISTERE' | 'CAMPUS'

// ============================================================
// 3. TYPES ÉVÉNEMENTS FULLCALENDAR
// ============================================================

export interface PlanningEventMetadata {
  campus: string
  ministereId: string
  ministereLabel: string
  typeActivite: string
  statut: PlanningStatus
  membreIds: string[]
  responsableId: string
  /** Vrai si l'utilisateur connecté est affecté à cet événement */
  isPersonal?: boolean
  /** Couleur calculée pour le ministère organisateur */
  ministereColor?: MinistereColor
}

export interface PlanningEvent extends EventInput {
  id: string
  title: string
  start: string
  end?: string
  allDay?: boolean
  extendedProps: PlanningEventMetadata
}

// ============================================================
// 4. DTOs BACKEND — Miroir TypeScript des modèles Python
// ============================================================

// --- Activité ---

export interface ActiviteRead {
  id: string
  type: string
  date_debut: string
  date_fin: string
  lieu?: string | null
  description?: string | null
  campus_id: string
  ministere_organisateur_id: string
}

export interface ActiviteCreate {
  type: string
  date_debut: string
  date_fin: string
  lieu?: string
  description?: string
  campus_id: string
  ministere_organisateur_id: string
}

export interface ActiviteUpdate {
  type?: string
  date_debut?: string
  date_fin?: string
  lieu?: string
  description?: string
}

// --- Membre résumé (dans les affectations) ---

export interface MemberSummaryRead {
  id: string
  nom: string
  prenom: string
}

// --- Affectations ---

export interface AffectationSimpleCreate {
  membre_id: string
  role_code: string
}

export interface AffectationFullUpdate {
  id?: string
  membre_id: string
  role_code: string
  statut_affectation_code?: string
}

export interface AffectationFullRead {
  id: string
  statut_affectation_code: string
  role_code: string
  membre?: MemberSummaryRead | null
}

// --- Slots ---

export interface SlotFullNested {
  nom_creneau: string
  date_debut: string
  date_fin: string
  affectations: AffectationSimpleCreate[]
}

export interface SlotFullUpdate {
  id?: string
  nom_creneau: string
  date_debut: string
  date_fin: string
  affectations: AffectationFullUpdate[]
}

export interface SlotFullRead {
  id: string
  nom_creneau: string
  date_debut: string
  date_fin: string
  nb_personnes_requis: number
  affectations: AffectationFullRead[]
  /** Calculé côté backend : (nb affectés / nb_personnes_requis) * 100 */
  filling_rate: number
}

// --- Contexte workflow ---

export interface ViewContext {
  allowed_transitions: string[]
  total_slots: number
  filled_slots: number
  is_ready_for_publish: boolean
}

// --- Planning complet ---

export interface PlanningFullRead {
  id: string
  statut_code: PlanningStatus
  activite_id?: string | null
  activite?: ActiviteRead | null
  slots: SlotFullRead[]
  view_context?: ViewContext | null
}

export interface PlanningFullCreate {
  activite: ActiviteCreate
  slots: SlotFullNested[]
}

export interface PlanningFullUpdate {
  activite?: ActiviteUpdate
  slots?: SlotFullUpdate[]
}

// --- Agenda personnel (GET /plannings/my) ---

export interface CampusFilterParams {
  ministereId?: string
  statutCode?: string
  start?: string
  end?: string
}
