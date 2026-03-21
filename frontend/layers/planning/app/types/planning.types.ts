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
  { bg: '#F59E0B', text: '#78350F', light: '#FFFBEB', border: '#FCD34D' }, // ambre — WCAG AA
  { bg: '#8B5CF6', text: '#FFFFFF', light: '#F5F3FF', border: '#C4B5FD' }, // violet
  { bg: '#EF4444', text: '#FFFFFF', light: '#FEF2F2', border: '#FCA5A5' }, // rouge
  { bg: '#06B6D4', text: '#FFFFFF', light: '#ECFEFF', border: '#67E8F9' }, // cyan
  { bg: '#F97316', text: '#7C2D12', light: '#FFF7ED', border: '#FDBA74' }, // orange — WCAG AA
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

/** Correspond aux valeurs de l'enum AffectationStatusCode côté backend */
export type AffectationStatus = 'PROPOSE' | 'CONFIRME' | 'REFUSE' | 'PRESENT' | 'ABSENT' | 'RETARD'

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
  /** Membres affectés avec noms résolus (pour affichage drawer) */
  membres?: Array<{ id: string; prenom: string; nom: string }>
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

export interface ActiviteFullRead extends ActiviteRead {
  campus_nom?: string | null
  ministere_organisateur_nom?: string | null
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
  campus_id?: string
  ministere_organisateur_id?: string
}

// --- Vue membre de ses propres affectations ---

export interface AffectationMemberRead {
  id: string
  statut_affectation_code: AffectationStatus
  role_code: string
  slot_nom: string
  slot_debut: string
  slot_fin: string
  activite_type?: string | null
  ministere_nom?: string | null
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
  ministere_id?: string | null
}

export interface AffectationFullUpdate {
  id?: string
  membre_id: string
  role_code: string
  statut_affectation_code?: string
  ministere_id?: string | null
}

export interface AffectationFullRead {
  id: string
  statut_affectation_code: string
  role_code: string
  membre?: MemberSummaryRead | null
  ministere_id?: string | null
  ministere_nom?: string | null
}

// --- Slots ---

export interface SlotFullNested {
  nom_creneau: string
  date_debut: string
  date_fin: string
  nb_personnes_requis?: number
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
  template_id?: string | null
  activite?: ActiviteFullRead | null
  slots: SlotFullRead[]
  view_context?: ViewContext | null
}

export interface PlanningFullCreate {
  activite: ActiviteCreate
  slots: SlotFullNested[]
  template_id?: string | null
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

// ============================================================
// 5. TYPES FORMULAIRE — usage interne PlanningFormModal
// ============================================================

/** Membre simplifié pour l'autocomplete */
export interface MembreSimple {
  id: string
  nom: string
  prenom: string
  email?: string | null
  actif: boolean
}

/** Rôle de compétence pour le select affectation */
export interface RoleCompetenceRead {
  code: string
  libelle: string
  categorie_code: string
}

// ============================================================
// 6. TEAM — GET /campus/{campus_id}/team
// ============================================================

export interface TeamMemberRead {
  id: string
  nom: string
  prenom: string
  roles: string[] // liste de role_code
}

export interface TeamMinistereRead {
  id: string
  nom: string
  membres: TeamMemberRead[]
}

export interface CampusTeamRead {
  ministeres: TeamMinistereRead[]
}

// ============================================================
// 7. PLANNING TEMPLATES — US-01
// ============================================================

export interface PlanningTemplateRoleRead {
  id: string
  role_code: string
}

export interface PlanningTemplateSlotRead {
  id: string
  nom_creneau: string
  offset_debut_minutes: number
  offset_fin_minutes: number
  nb_personnes_requis: number
  roles: PlanningTemplateRoleRead[]
}

export interface PlanningTemplateRead {
  id: string
  nom: string
  description?: string | null
  activite_type: string
  duree_minutes: number
  campus_id: string
  ministere_id: string
  created_by_id: string
  created_at: string
  used_count: number
  slots: PlanningTemplateSlotRead[]
}

export interface SaveAsTemplateRequest {
  nom: string
  description?: string | null
}

export interface PlanningTemplateUpdate {
  nom?: string | null
  description?: string | null
}

/** Item affectation dans le formulaire */
export interface AffectationFormItem {
  _tempId: string
  id?: string
  membre_id: string
  membre_prenom: string
  membre_nom: string
  role_code: string
  ministere_id: string
  statut_affectation_code?: AffectationStatus
}

/** Slot dans le formulaire */
export interface SlotFormItem {
  _tempId: string
  id?: string
  nom_creneau: string
  heure_debut: string
  heure_fin: string
  nb_personnes_requis: number
  affectations: AffectationFormItem[]
}

/** État interne de la section activité */
export interface ActiviteFormState {
  type: string
  date_debut: string
  date_fin: string
  lieu: string
  description: string
  campus_id: string
  ministere_organisateur_id: string
}

/** Types d'activité disponibles */
export const ACTIVITE_TYPES = [
  'Culte',
  'Répétition',
  'Conférence',
  'Formation',
  'Réunion',
  'Jeunesse',
  'Soirée Louange',
  'Événement spécial',
] as const
