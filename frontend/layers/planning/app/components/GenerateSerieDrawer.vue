<script setup lang="ts">
import { computed, watch } from 'vue'
import type { GenerateSeriesForm, GenerateSeriesResponse } from '../types/planning.types'
import { useSerieForm } from '../composables/useSerieForm'
import SerieParamsForm from './serie/SerieParamsForm.vue'
import SeriePreviewList from './serie/SeriePreviewList.vue'
import SerieResultPanel from './serie/SerieResultPanel.vue'

const props = defineProps<{
  templateId: string | null
  templateNom: string
}>()

const emit = defineEmits<{
  close: []
  generated: [result: GenerateSeriesResponse]
}>()

const { form, preview, isLoadingPreview, isGenerating, result, formError, submitGenerate, reset } =
  useSerieForm(() => props.templateId)

function applyFormPatch(patch: Partial<GenerateSeriesForm>) {
  Object.assign(form, patch)
}

const canGenerate = computed(
  () => !!preview.value && preview.value.total > 0 && !isGenerating.value,
)

async function handleGenerate() {
  const res = await submitGenerate()
  if (res) emit('generated', res)
}

function handleClose() {
  reset()
  emit('close')
}

watch(
  () => props.templateId,
  (id) => {
    if (id) reset()
  },
)
</script>

<template>
  <AppDrawer
    :isOpen="templateId !== null"
    :title="`Générer une série — ${templateNom}`"
    initialSize="standard"
    @close="handleClose"
  >
    <div class="space-y-6">
      <!-- Résultat post-génération -->
      <SerieResultPanel v-if="result" :result="result" />

      <template v-else>
        <!-- Zone 1 : paramètres -->
        <SerieParamsForm :form="form" @update:form="applyFormPatch" />

        <!-- Zone 2 : prévisualisation -->
        <div v-if="preview || isLoadingPreview" class="border-t border-(--color-neutral-100) pt-4">
          <p class="mb-3 text-xs font-semibold tracking-wide text-(--color-neutral-500) uppercase">
            Prévisualisation
          </p>
          <SeriePreviewList v-if="preview" :preview="preview" :isLoading="isLoadingPreview" />
          <div v-else class="space-y-2">
            <div
              v-for="i in 4"
              :key="i"
              class="h-7 animate-pulse rounded-lg bg-(--color-neutral-100)"
            />
          </div>
        </div>

        <!-- Erreur -->
        <p v-if="formError" class="text-sm text-red-600">{{ formError }}</p>
      </template>
    </div>

    <template #footer>
      <div class="flex items-center justify-between">
        <button
          type="button"
          class="rounded-lg border border-(--color-neutral-200) px-4 py-2 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50)"
          @click="handleClose"
        >
          {{ result ? 'Fermer' : 'Annuler' }}
        </button>
        <button
          v-if="!result"
          type="button"
          :disabled="!canGenerate"
          class="btn btn-primary"
          @click="handleGenerate"
        >
          <span v-if="isGenerating">Génération…</span>
          <span v-else>
            Générer {{ preview?.total ?? '' }} planning{{ (preview?.total ?? 0) > 1 ? 's' : '' }}
          </span>
        </button>
      </div>
    </template>
  </AppDrawer>
</template>
