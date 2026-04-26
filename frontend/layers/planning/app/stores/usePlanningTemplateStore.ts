import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usePagination } from '~~/layers/base/app/stores/utils/usePagination'
import { PlanningRepository } from '../repositories/PlanningRepository'
import type {
  GenerateSeriesForm,
  GenerateSeriesResponse,
  PlanningTemplateCreate,
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

  const {
    pagination,
    total,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    setTotal,
    goToPage,
    resetPagination,
  } = usePagination(20)

  async function createTemplate(
    payload: PlanningTemplateCreate,
  ): Promise<PlanningTemplateReadFull> {
    const tpl = await repo.createTemplate(payload)
    notify.success(`"${tpl.nom}" créé`)
    return tpl
  }

  async function fetchTemplates(ministereId?: string): Promise<void> {
    isLoading.value = true
    try {
      const res = await repo.listTemplates(ministereId, {
        limit: pagination.limit,
        offset: pagination.offset,
      })
      templates.value = res.data
      setTotal(res.total)
    } catch (err) {
      notify.error('Impossible de charger les templates')
      throw err
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
    pagination,
    total,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    goToPage,
    resetPagination,
    createTemplate,
    fetchTemplates,
    fetchTemplate,
    updateTemplate,
    duplicateTemplate,
    deleteTemplate,
    generateSeries,
  }
})
