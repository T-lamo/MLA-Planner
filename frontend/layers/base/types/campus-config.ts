import type { RoleCompetenceRead } from './role-competence'

// ---- Requêtes (alignées sur les schémas Pydantic backend) ----

export interface MinistereConfigCreate {
  nom: string
  description?: string
}

export interface CategorieConfigCreate {
  nom: string
  description?: string
}

export interface RoleCompetenceConfigCreate {
  code: string
  libelle: string
  description?: string
}

export interface MinistereConfigUpdate {
  nom?: string
  description?: string
}

export interface CategorieConfigUpdate {
  nom?: string
  description?: string
}

export interface RoleCompetenceConfigUpdate {
  libelle?: string
  description?: string
}

// ---- Entités backend (lectures) ----

export interface MinistereRead {
  id: string
  nom: string
  actif: boolean
  date_creation?: string
  description?: string
}

export interface CategorieRoleRead {
  code: string
  libelle: string
  description?: string
  ministere_id?: string
}

export interface RoleRead {
  id: string
  libelle: string
}

// ---- Réponses enrichies des endpoints /config ----

export interface MinistereConfigResponse {
  ministere: MinistereRead
  created: boolean
  linked: boolean
}

export interface CategorieConfigResponse {
  categorie: CategorieRoleRead
  created: boolean
}

export interface RoleCompetenceConfigResponseItem {
  code: string
  libelle: string
  description?: string
  categorie_code: string
}

export interface RoleCompetenceConfigApiResponse {
  role_competence: RoleCompetenceConfigResponseItem
  created: boolean
}

export interface RbacRolesInitResponse {
  roles: RoleRead[]
  created_count: number
}

export interface StatutsInitResponse {
  statuts_planning: string[]
  statuts_affectation: string[]
}

// ---- Structure du résumé campus ----

export interface CampusSummaryCategorie {
  code: string
  libelle: string
  description?: string
  roles_actifs?: RoleCompetenceRead[]
}

export interface CampusSummaryMinistere {
  id: string
  nom: string
  description?: string
  categories: CampusSummaryCategorie[]
}

export interface CampusConfigSummary {
  campus_id: string
  campus_nom: string
  ministeres: CampusSummaryMinistere[]
  statuts_planning: string[]
  statuts_affectation: string[]
}

// ---- Setup campus (opération complète) ----

export interface RoleSetupItem {
  code: string
  libelle: string
  description?: string
}

export interface CategorieSetupItem {
  nom: string
  description?: string
  roles: RoleSetupItem[]
}

export interface MinistereSetupItem {
  nom: string
  description?: string
  init_rbac: boolean
  categories: CategorieSetupItem[]
}

export interface CampusSetupPayload {
  init_statuts: boolean
  ministeres: MinistereSetupItem[]
}

export interface CampusSetupResult {
  campus_id: string
  ministeres_created: number
  ministeres_linked: number
  categories_created: number
  roles_created: number
  rbac_roles_created: number
  statuts_initialises: boolean
  summary: CampusConfigSummary
}

// ---- MinistereRoleConfig (RC-160) ----

export interface MinistereRoleConfigRead {
  ministere_id: string
  role_code: string
}

export interface MinistereRoleConfigResponse {
  config: MinistereRoleConfigRead
  created: boolean
}

export interface MinistereRolesListResponse {
  ministere_id: string
  roles: RoleCompetenceRead[]
}

export interface CategorieWithActiveRoles {
  categorie: CategorieRoleRead
  roles_actifs: RoleCompetenceRead[]
}

export interface BatchActivateResult {
  categorie_code: string
  roles_actives: number
}

// ---- UI ----

export type CampusConfigDrawerMode =
  | 'add-ministere'
  | 'add-categorie'
  | 'add-role'
  | 'edit-ministere'
  | 'edit-categorie'
  | 'edit-role'
  | null

export interface CampusConfigDrawerContext {
  mode: CampusConfigDrawerMode
  ministereId?: string
  categorieId?: string
  roleCode?: string
}
