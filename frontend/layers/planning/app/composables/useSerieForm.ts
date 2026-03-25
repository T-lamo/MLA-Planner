import { reactive, ref, watch } from 'vue'
import type {
  GenerateSeriesForm,
  GenerateSeriesResponse,
  SeriesPreviewResponse,
} from '../types/planning.types'
import { PlanningRepository } from '../repositories/PlanningRepository'

export function useSerieForm(templateId: () => string | null) {
  const repo = new PlanningRepository()

  const form = reactive<GenerateSeriesForm>({
    date_debut: '',
    date_fin: '',
    recurrence: 'HEBDOMADAIRE',
    jour_semaine: 1,
  })

  const preview = ref<SeriesPreviewResponse | null>(null)
  const isLoadingPreview = ref(false)
  const isGenerating = ref(false)
  const result = ref<GenerateSeriesResponse | null>(null)
  const formError = ref<string | null>(null)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  watch(
    () => ({ ...form }),
    async () => {
      if (!form.date_debut || !form.date_fin) return
      if (form.recurrence === 'HEBDOMADAIRE' && form.jour_semaine === null) return
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(async () => {
        isLoadingPreview.value = true
        try {
          preview.value = await repo.previewSeries(form)
          formError.value = null
        } catch (e: unknown) {
          preview.value = null
          formError.value =
            (e as { message?: string })?.message ?? 'Erreur lors de la prévisualisation'
        } finally {
          isLoadingPreview.value = false
        }
      }, 300)
    },
    { deep: true },
  )

  async function submitGenerate(): Promise<GenerateSeriesResponse | null> {
    const id = templateId()
    if (!id || !preview.value || preview.value.total === 0) return null
    isGenerating.value = true
    formError.value = null
    try {
      result.value = await repo.generateSeries(id, form)
      return result.value
    } catch (e: unknown) {
      formError.value = (e as { message?: string })?.message ?? 'Erreur lors de la génération'
      return null
    } finally {
      isGenerating.value = false
    }
  }

  function reset() {
    form.date_debut = ''
    form.date_fin = ''
    form.recurrence = 'HEBDOMADAIRE'
    form.jour_semaine = 1
    preview.value = null
    result.value = null
    formError.value = null
  }

  return {
    form,
    preview,
    isLoadingPreview,
    isGenerating,
    result,
    formError,
    submitGenerate,
    reset,
  }
}
