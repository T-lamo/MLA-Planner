import { defineStore } from 'pinia'
import { ref } from 'vue'
import { PlanningRepository } from '../repositories/PlanningRepository'
import type {
  GenerateSeriesForm,
  GenerateSeriesResponse,
  PlanningTemplateFullUpdate,
  PlanningTemplateListItem,
  PlanningTemplateReadFull,
} from '../types/planning.types'

export const usePlanningTemplateStore = defineStore('planningTemplates', () => {
  const repo = new PlanningRepository()
  const notify = useMLANotify()

  const templates = ref<PlanningTemplateListItem[]>([])
  const selectedTemplate = ref<PlanningTemplateReadFull | null>(null)
  const isLoading = ref(false)

  async function fetchTemplates(ministereId?: string): Promise<void> {
    isLoading.value = true
    try {
      templates.value = await repo.listTemplates(ministereId)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTemplate(id: string): Promise<void> {
    isLoading.value = true
    try {
      selectedTemplate.value = await repo.getTemplateFull(id)
    } finally {
      isLoading.value = false
    }
  }

  async function updateTemplate(id: string, payload: PlanningTemplateFullUpdate): Promise<void> {
    const updated = await repo.updateTemplateFull(id, payload)
    selectedTemplate.value = updated
    const idx = templates.value.findIndex((t) => t.id === id)
    if (idx !== -1) {
      templates.value[idx] = {
        ...templates.value[idx]!,
        nom: updated.nom,
        description: updated.description ?? null,
        nb_creneaux: updated.slots.length,
        visibilite: updated.visibilite,
      }
    }
    notify.success('Template mis à jour')
  }

  async function duplicateTemplate(id: string): Promise<PlanningTemplateListItem> {
    const copy = await repo.duplicateTemplate(id)
    templates.value.unshift(copy)
    notify.success(`"${copy.nom}" créé`)
    return copy
  }

  async function deleteTemplate(id: string): Promise<void> {
    const idx = templates.value.findIndex((t) => t.id === id)
    const backup = idx !== -1 ? templates.value[idx] : null
    if (idx !== -1) templates.value.splice(idx, 1)
    try {
      await repo.deleteTemplate(id)
      notify.success('Template supprimé')
    } catch (err) {
      if (backup && idx !== -1) templates.value.splice(idx, 0, backup)
      notify.error('Erreur lors de la suppression')
      throw err
    }
  }

  async function generateSeries(
    templateId: string,
    form: GenerateSeriesForm,
  ): Promise<GenerateSeriesResponse> {
    return repo.generateSeries(templateId, form)
  }

  return {
    templates,
    selectedTemplate,
    isLoading,
    fetchTemplates,
    fetchTemplate,
    updateTemplate,
    duplicateTemplate,
    deleteTemplate,
    generateSeries,
  }
})
