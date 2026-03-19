import { ref, computed } from 'vue'
import type { CampusRead } from '~~/layers/base/types/campus'
import type {
  CampusConfigSummary,
  CampusSetupPayload,
  CampusSetupResult,
  CampusSummaryCategorie,
  CampusSummaryMinistere,
  CategorieConfigCreate,
  CategorieConfigUpdate,
  MinistereConfigCreate,
  MinistereConfigUpdate,
  MinistereRead,
  RoleCompetenceConfigCreate,
  RoleCompetenceConfigUpdate,
} from '~~/layers/base/types/campus-config'
import type { RoleCompetenceRead, RolesByCategoryItem } from '~~/layers/base/types/role-competence'
import { CampusConfigRepository } from '../repositories/CampusConfigRepository'
import { RoleCompetenceRepository } from '../repositories/RoleCompetenceRepository'

// -----------------------------------------------------------------------
// Module-level singletons — état partagé entre tous les composants
// -----------------------------------------------------------------------

const campuses = ref<CampusRead[]>([])
const selectedCampusId = ref<string>('')
const summary = ref<CampusConfigSummary | null>(null)
const allRoleCompetences = ref<RoleCompetenceRead[]>([])
const allMinisteres = ref<MinistereRead[]>([])
const isLoading = ref(false)

const repo = new CampusConfigRepository()
const rcRepo = new RoleCompetenceRepository()

// -----------------------------------------------------------------------
// Composable exporté
// -----------------------------------------------------------------------

export const useCampusConfig = () => {
  const notify = useMLANotify()

  // -----------------------------------------------------------------------
  // Computed
  // -----------------------------------------------------------------------

  const selectedCampus = computed<CampusRead | null>(
    () => campuses.value.find((c) => c.id === selectedCampusId.value) ?? null,
  )

  const ministeres = computed<CampusSummaryMinistere[]>(() => summary.value?.ministeres ?? [])

  function categoriesForMinistere(ministereId: string): CampusSummaryCategorie[] {
    return ministeres.value.find((m) => m.id === ministereId)?.categories ?? []
  }

  function rolesForCategorie(categorieId: string): RoleCompetenceRead[] {
    return allRoleCompetences.value.filter((r) => r.categorie_code === categorieId)
  }

  // -----------------------------------------------------------------------
  // Chargement interne (sans notification — le intercepteur useApiFetch gère)
  // -----------------------------------------------------------------------

  async function refreshSummary(): Promise<void> {
    if (!selectedCampusId.value) return
    try {
      summary.value = await repo.getCampusSummary(selectedCampusId.value)
    } catch {
      // Erreur déjà notifiée par l'intercepteur useApiFetch
    }
  }

  async function refreshRoleCompetences(): Promise<void> {
    try {
      const items: RolesByCategoryItem[] = await rcRepo.getByCategory()
      allRoleCompetences.value = items.flatMap((item) => item.roles)
    } catch {
      // Non bloquant
    }
  }

  async function refreshAllMinisteres(): Promise<void> {
    try {
      allMinisteres.value = await repo.getAllMinisteres()
    } catch {
      // Non bloquant
    }
  }

  // -----------------------------------------------------------------------
  // Actions publiques
  // -----------------------------------------------------------------------

  async function loadCampuses(): Promise<void> {
    isLoading.value = true
    try {
      campuses.value = await repo.listCampuses()
      if (campuses.value.length > 0 && !selectedCampusId.value) {
        selectedCampusId.value = campuses.value[0]!.id
      }
      await Promise.all([refreshSummary(), refreshRoleCompetences(), refreshAllMinisteres()])
    } catch {
      // Erreur déjà notifiée par l'intercepteur useApiFetch
    } finally {
      isLoading.value = false
    }
  }

  async function selectCampus(id: string): Promise<void> {
    selectedCampusId.value = id
    isLoading.value = true
    try {
      await refreshSummary()
    } finally {
      isLoading.value = false
    }
  }

  async function addMinistere(payload: MinistereConfigCreate): Promise<void> {
    await repo.addMinistere(selectedCampusId.value, payload)
    notify.success('Ministère ajouté')
    await refreshSummary()
  }

  async function removeMinistere(ministereId: string): Promise<void> {
    await repo.removeMinistere(selectedCampusId.value, ministereId)
    notify.success('Lien supprimé')
    await refreshSummary()
  }

  async function addCategorie(ministereId: string, payload: CategorieConfigCreate): Promise<void> {
    await repo.addCategorie(ministereId, payload)
    notify.success('Catégorie ajoutée')
    await refreshSummary()
  }

  async function deleteCategorie(ministereId: string, categorieId: string): Promise<void> {
    await repo.deleteCategorie(ministereId, categorieId)
    notify.success('Catégorie supprimée')
    await refreshSummary()
  }

  async function linkMinistere(ministereNom: string): Promise<void> {
    await repo.addMinistere(selectedCampusId.value, { nom: ministereNom })
    notify.success('Ministère rattaché au campus')
    await Promise.all([refreshSummary(), refreshAllMinisteres()])
  }

  async function addRoleCompetence(
    categorieId: string,
    payload: RoleCompetenceConfigCreate,
  ): Promise<void> {
    await repo.addRoleCompetence(categorieId, payload)
    notify.success('Compétence ajoutée')
    await Promise.all([refreshSummary(), refreshRoleCompetences()])
  }

  async function deleteRoleCompetence(categorieId: string, roleCode: string): Promise<void> {
    await repo.deleteRoleCompetence(categorieId, roleCode)
    notify.success('Compétence supprimée')
    await refreshRoleCompetences()
  }

  async function linkRoleCompetence(categorieId: string, roleCode: string): Promise<void> {
    await repo.linkRoleCompetence(categorieId, roleCode)
    notify.success('Compétence rattachée')
    await Promise.all([refreshSummary(), refreshRoleCompetences()])
  }

  async function updateMinistere(
    ministereId: string,
    payload: MinistereConfigUpdate,
  ): Promise<void> {
    await repo.updateMinistere(ministereId, payload)
    notify.success('Ministère mis à jour')
    await refreshSummary()
  }

  async function updateCategorie(
    ministereId: string,
    categorieId: string,
    payload: CategorieConfigUpdate,
  ): Promise<void> {
    await repo.updateCategorie(ministereId, categorieId, payload)
    notify.success('Catégorie mise à jour')
    await refreshSummary()
  }

  async function updateRoleCompetence(
    categorieId: string,
    roleCode: string,
    payload: RoleCompetenceConfigUpdate,
  ): Promise<void> {
    await repo.updateRoleCompetence(categorieId, roleCode, payload)
    notify.success('Compétence mise à jour')
    await refreshRoleCompetences()
  }

  async function initRbac(ministereId: string): Promise<void> {
    const result = await repo.initRbacRoles(selectedCampusId.value, ministereId)
    notify.success(`Rôles RBAC initialisés (${result.created_count} créé(s))`)
  }

  async function initStatuts(): Promise<void> {
    await repo.initStatuts()
    notify.success('Statuts initialisés')
    await refreshSummary()
  }

  async function setupCampus(payload: CampusSetupPayload): Promise<CampusSetupResult> {
    const result = await repo.setupCampus(selectedCampusId.value, payload)
    const parts: string[] = []
    if (result.ministeres_created > 0) parts.push(`${result.ministeres_created} min.`)
    if (result.categories_created > 0) parts.push(`${result.categories_created} cat.`)
    if (result.roles_created > 0) parts.push(`${result.roles_created} rôles`)
    const detail = parts.length > 0 ? ` — ${parts.join(', ')} créé(s)` : ''
    notify.success(`Campus configuré${detail}`)
    await Promise.all([refreshSummary(), refreshRoleCompetences()])
    return result
  }

  return {
    // État réactif
    campuses,
    selectedCampusId,
    summary,
    allRoleCompetences,
    allMinisteres,
    isLoading,

    // Computed
    selectedCampus,
    ministeres,

    // Fonctions dérivées
    categoriesForMinistere,
    rolesForCategorie,

    // Actions
    loadCampuses,
    selectCampus,
    addMinistere,
    linkMinistere,
    removeMinistere,
    addCategorie,
    deleteCategorie,
    addRoleCompetence,
    deleteRoleCompetence,
    linkRoleCompetence,
    updateMinistere,
    updateCategorie,
    updateRoleCompetence,
    initRbac,
    initStatuts,
    setupCampus,
  }
}
