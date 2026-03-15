import { ref, reactive } from 'vue'
import type {
  CampusConfigDrawerContext,
  CampusConfigDrawerMode,
  CategorieConfigCreate,
  CategorieConfigUpdate,
  MinistereConfigCreate,
  MinistereConfigUpdate,
  RoleCompetenceConfigCreate,
  RoleCompetenceConfigUpdate,
} from '~~/layers/base/types/campus-config'
import type { useCampusConfig } from './useCampusConfig'

// -----------------------------------------------------------------------
// Module-level singletons — état partagé entre tiroir et vue
// -----------------------------------------------------------------------

const drawerContext = ref<CampusConfigDrawerContext>({ mode: null })
const isSubmitting = ref(false)

const ministereForm = reactive<MinistereConfigCreate>({ nom: '', description: '' })
const categorieForm = reactive<CategorieConfigCreate>({ nom: '', description: '' })
const roleForm = reactive<RoleCompetenceConfigCreate>({ code: '', libelle: '', description: '' })

// -----------------------------------------------------------------------
// Composable exporté
// -----------------------------------------------------------------------

export const useCampusConfigForm = () => {
  function resetForms(): void {
    ministereForm.nom = ''
    ministereForm.description = ''
    categorieForm.nom = ''
    categorieForm.description = ''
    roleForm.code = ''
    roleForm.libelle = ''
    roleForm.description = ''
  }

  function openAddMinistere(): void {
    resetForms()
    drawerContext.value = { mode: 'add-ministere' }
  }

  function openAddCategorie(ministereId: string): void {
    resetForms()
    drawerContext.value = { mode: 'add-categorie', ministereId }
  }

  function openAddRole(ministereId: string, categorieId: string): void {
    resetForms()
    drawerContext.value = { mode: 'add-role', ministereId, categorieId }
  }

  function openEditMinistere(
    ministereId: string,
    currentNom: string,
    currentDescription?: string,
  ): void {
    resetForms()
    ministereForm.nom = currentNom
    ministereForm.description = currentDescription ?? ''
    drawerContext.value = { mode: 'edit-ministere', ministereId }
  }

  function openEditCategorie(
    ministereId: string,
    categorieId: string,
    currentNom: string,
    currentDescription?: string,
  ): void {
    resetForms()
    categorieForm.nom = currentNom
    categorieForm.description = currentDescription ?? ''
    drawerContext.value = { mode: 'edit-categorie', ministereId, categorieId }
  }

  function openEditRole(
    categorieId: string,
    roleCode: string,
    currentLibelle: string,
    currentDescription?: string,
  ): void {
    resetForms()
    roleForm.code = roleCode
    roleForm.libelle = currentLibelle
    roleForm.description = currentDescription ?? ''
    drawerContext.value = { mode: 'edit-role', categorieId, roleCode }
  }

  function closeDrawer(): void {
    drawerContext.value = { mode: null }
    isSubmitting.value = false
  }

  async function submitForm(campusConfig: ReturnType<typeof useCampusConfig>): Promise<void> {
    if (isSubmitting.value) return
    isSubmitting.value = true
    const mode: CampusConfigDrawerMode = drawerContext.value.mode

    try {
      if (mode === 'add-ministere') {
        await campusConfig.addMinistere({ ...ministereForm })
      } else if (mode === 'add-categorie' && drawerContext.value.ministereId) {
        await campusConfig.addCategorie(drawerContext.value.ministereId, { ...categorieForm })
      } else if (
        mode === 'add-role' &&
        drawerContext.value.ministereId &&
        drawerContext.value.categorieId
      ) {
        await campusConfig.addRoleCompetence(drawerContext.value.categorieId, { ...roleForm })
      } else if (mode === 'edit-ministere' && drawerContext.value.ministereId) {
        const payload: MinistereConfigUpdate = {
          nom: ministereForm.nom || undefined,
          description: ministereForm.description || undefined,
        }
        await campusConfig.updateMinistere(drawerContext.value.ministereId, payload)
      } else if (
        mode === 'edit-categorie' &&
        drawerContext.value.ministereId &&
        drawerContext.value.categorieId
      ) {
        const payload: CategorieConfigUpdate = {
          nom: categorieForm.nom || undefined,
          description: categorieForm.description || undefined,
        }
        await campusConfig.updateCategorie(
          drawerContext.value.ministereId,
          drawerContext.value.categorieId,
          payload,
        )
      } else if (
        mode === 'edit-role' &&
        drawerContext.value.categorieId &&
        drawerContext.value.roleCode
      ) {
        const payload: RoleCompetenceConfigUpdate = {
          libelle: roleForm.libelle || undefined,
          description: roleForm.description || undefined,
        }
        await campusConfig.updateRoleCompetence(
          drawerContext.value.categorieId,
          drawerContext.value.roleCode,
          payload,
        )
      }
      closeDrawer()
    } catch {
      // L'erreur est déjà notifiée par l'intercepteur useApiFetch
    } finally {
      isSubmitting.value = false
    }
  }

  return {
    // État du drawer
    drawerContext,
    isSubmitting,

    // Formulaires
    ministereForm,
    categorieForm,
    roleForm,

    // Actions
    openAddMinistere,
    openAddCategorie,
    openAddRole,
    openEditMinistere,
    openEditCategorie,
    openEditRole,
    closeDrawer,
    resetForms,
    submitForm,
  }
}
