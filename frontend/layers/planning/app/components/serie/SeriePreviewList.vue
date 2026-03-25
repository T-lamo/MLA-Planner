<script setup lang="ts">
import { AlertTriangle } from 'lucide-vue-next'
import type { SeriesPreviewResponse } from '../../types/planning.types'
import { useSerieDate } from '../../composables/useSerieDate'

defineProps<{
  preview: SeriesPreviewResponse
  isLoading: boolean
}>()

const { formatSerieDate, semaineNum } = useSerieDate({
  date_debut: '',
  date_fin: '',
  recurrence: 'HEBDOMADAIRE',
  jour_semaine: null,
})
</script>

<template>
  <div class="space-y-3">
    <!-- Skeleton chargement -->
    <template v-if="isLoading">
      <div v-for="i in 3" :key="i" class="h-8 animate-pulse rounded-lg bg-(--color-neutral-100)" />
    </template>

    <template v-else>
      <!-- Résumé -->
      <p class="text-sm font-medium text-(--color-neutral-700)">
        {{ preview.total }} date{{ preview.total > 1 ? 's' : '' }} générée{{
          preview.total > 1 ? 's' : ''
        }}
      </p>

      <!-- Conflits -->
      <div v-if="preview.conflits.length > 0" class="space-y-1.5">
        <div
          v-for="c in preview.conflits"
          :key="c.date"
          class="flex items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-xs"
        >
          <AlertTriangle class="size-3.5 shrink-0 text-orange-500" />
          <span class="text-orange-800">
            <strong>{{ formatSerieDate(c.date) }}</strong> — planning existant :
            <NuxtLink :to="`/planning/${c.planning_id}`" class="underline hover:text-orange-900">
              {{ c.planning_titre }}
            </NuxtLink>
          </span>
        </div>
      </div>

      <!-- Liste des dates -->
      <div class="max-h-48 space-y-1 overflow-y-auto">
        <div
          v-for="d in preview.dates"
          :key="d"
          class="flex items-center justify-between rounded-lg bg-(--color-neutral-50) px-3 py-1.5 text-sm"
        >
          <span class="text-(--color-neutral-800) capitalize">
            {{ formatSerieDate(d) }}
          </span>
          <span class="text-xs text-(--color-neutral-400)"> Sem. {{ semaineNum(d) }} </span>
        </div>
      </div>
    </template>
  </div>
</template>
