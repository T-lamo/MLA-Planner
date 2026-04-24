<template>
  <div
    v-if="totalPages > 1 || total > 0"
    class="flex flex-wrap items-center justify-between gap-3 pt-3"
  >
    <!-- Total résultats -->
    <span class="text-sm text-slate-500"> {{ total }} résultat{{ total > 1 ? 's' : '' }} </span>

    <!-- Numéros de pages + navigation -->
    <div class="flex items-center gap-1">
      <!-- Précédent -->
      <button
        class="btn btn-ghost btn-sm btn-icon"
        :disabled="currentPage === 1 || loading"
        aria-label="Page précédente"
        @click="emit('change', currentPage - 1)"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>

      <!-- Fenêtre glissante de numéros -->
      <template v-for="page in visiblePages" :key="page">
        <span v-if="page === '...'" class="px-1 text-sm text-slate-400">…</span>
        <button
          v-else
          class="btn btn-sm btn-icon"
          :class="page === currentPage ? 'btn-primary' : 'btn-ghost'"
          :disabled="loading"
          @click="emit('change', page as number)"
        >
          {{ page }}
        </button>
      </template>

      <!-- Suivant -->
      <button
        class="btn btn-ghost btn-sm btn-icon"
        :disabled="currentPage === totalPages || loading"
        aria-label="Page suivante"
        @click="emit('change', currentPage + 1)"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>
    </div>

    <!-- Page X / Y -->
    <span class="text-sm text-slate-400"> Page {{ currentPage }} / {{ totalPages }} </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    currentPage: number
    totalPages: number
    total: number
    pageSize?: number
    loading?: boolean
  }>(),
  {
    pageSize: 20,
    loading: false,
  },
)

const emit = defineEmits<{
  change: [page: number]
}>()

const visiblePages = computed<(number | '...')[]>(() => {
  const total = props.totalPages
  const current = props.currentPage
  const pages: (number | '...')[] = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
    return pages
  }

  pages.push(1)

  if (current > 3) pages.push('...')

  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)

  for (let i = start; i <= end; i++) pages.push(i)

  if (current < total - 2) pages.push('...')

  pages.push(total)

  return pages
})
</script>
