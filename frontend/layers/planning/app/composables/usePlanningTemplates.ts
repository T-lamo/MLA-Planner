import { ref, computed } from 'vue'
import { PlanningRepository } from '../repositories/PlanningRepository'
import type { PlanningTemplateRead, SaveAsTemplateRequest } from '../types/planning.types'

/**
 * Composable pour la gestion des templates de planning (US-01).
 * Expose les actions save, list et delete ainsi que les états de chargement.
 */
export function usePlanningTemplates() {
  const repo = new PlanningRepository()
  const notify = useMLANotify()
  const { handleError } = useFormError()

  const isSaving = ref(false)
  const isDeleting = ref(false)
  const templates = ref<PlanningTemplateRead[]>([])
  const templatesByMinistere = ref<PlanningTemplateRead[]>([])
  const templateError = ref<string | null>(null)

  const allAvailableTemplates = computed<PlanningTemplateRead[]>(() => {
    const map = new Map<string, PlanningTemplateRead>()
    for (const t of [...templates.value, ...templatesByMinistere.value]) {
      map.set(t.id, t)
    }
    return [...map.values()].sort((a, b) => b.used_count - a.used_count)
  })

  /**
   * Sauvegarde un planning existant comme template réutilisable.
   * Retourne le template créé, ou null en cas d'erreur.
   */
  async function saveAsTemplate(
    planningId: string,
    payload: SaveAsTemplateRequest,
  ): Promise<PlanningTemplateRead | null> {
    isSaving.value = true
    templateError.value = null
    try {
      const result = await repo.saveAsTemplate(planningId, payload)
      notify.success('Template créé', `"${result.nom}" a été enregistré.`)
      return result
    } catch (e) {
      templateError.value = handleError(e, 'Erreur lors de la création du template')
      return null
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Charge la liste des templates d'un campus dans `templates`.
   */
  async function loadByCampus(campusId: string): Promise<void> {
    templateError.value = null
    try {
      templates.value = await repo.listTemplatesByCampus(campusId)
    } catch (e) {
      templateError.value = handleError(e, 'Erreur lors du chargement des templates')
    }
  }

  /**
   * Charge la liste des templates d'un ministère dans `templatesByMinistere`.
   */
  async function loadByMinistere(ministereId: string): Promise<void> {
    try {
      templatesByMinistere.value = await repo.listTemplatesByMinistere(ministereId)
    } catch {
      templatesByMinistere.value = []
    }
  }

  /**
   * Supprime un template et retire-le de la liste locale.
   */
  async function deleteTemplate(templateId: string): Promise<boolean> {
    isDeleting.value = true
    templateError.value = null
    try {
      await repo.deleteTemplate(templateId)
      templates.value = templates.value.filter((t) => t.id !== templateId)
      notify.success('Template supprimé')
      return true
    } catch (e) {
      templateError.value = handleError(e, 'Erreur lors de la suppression du template')
      return false
    } finally {
      isDeleting.value = false
    }
  }

  return {
    isSaving,
    isDeleting,
    templates,
    templatesByMinistere,
    allAvailableTemplates,
    templateError,
    saveAsTemplate,
    loadByCampus,
    loadByMinistere,
    deleteTemplate,
  }
}
