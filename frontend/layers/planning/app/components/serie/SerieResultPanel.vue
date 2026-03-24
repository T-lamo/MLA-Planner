<script setup lang="ts">
import { CheckCircle2 } from 'lucide-vue-next'
import type { GenerateSeriesResponse } from '../../types/planning.types'
import { useSerieDate } from '../../composables/useSerieDate'

defineProps<{ result: GenerateSeriesResponse }>()

const { formatSerieDate } = useSerieDate({
  date_debut: '',
  date_fin: '',
  recurrence: 'HEBDOMADAIRE',
  jour_semaine: null,
})
</script>

<template>
  <div class="space-y-4">
    <!-- En-tête succès -->
    <div class="flex items-center gap-3 rounded-xl bg-green-50 px-4 py-3">
      <CheckCircle2 class="size-5 shrink-0 text-green-600" />
      <div>
        <p class="font-semibold text-green-800">
          {{ result.total }} planning{{ result.total > 1 ? 's' : '' }} créé{{
            result.total > 1 ? 's' : ''
          }}
          !
        </p>
        <p class="text-xs text-green-600">Série : {{ result.serie_id.slice(0, 8) }}…</p>
      </div>
    </div>

    <!-- Liste cliquable -->
    <div class="space-y-1">
      <NuxtLink
        v-for="p in result.plannings"
        :key="p.id"
        :to="`/planning/${p.id}`"
        class="flex items-center justify-between rounded-lg border border-(--color-neutral-200) px-3 py-2 text-sm hover:bg-(--color-neutral-50)"
      >
        <span class="text-(--color-neutral-800) capitalize">
          {{ formatSerieDate(p.date_debut) }}
        </span>
        <span class="text-xs text-(--color-neutral-400)">{{ p.statut }}</span>
      </NuxtLink>
    </div>
  </div>
</template>
