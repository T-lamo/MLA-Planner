<script setup lang="ts">
import { Music, ExternalLink, Youtube } from 'lucide-vue-next'
import type { PlanningChantRead } from '../types/planning.types'

interface Props {
  chants: PlanningChantRead[]
}

defineProps<Props>()
</script>

<template>
  <div v-if="chants.length > 0" class="flex flex-col gap-1.5">
    <RouterLink
      v-for="(chant, index) in chants"
      :key="chant.id"
      :to="`/songbook/${chant.id}`"
      class="group flex items-center gap-3 rounded-xl border border-slate-100 bg-white px-3 py-2.5 transition-all hover:border-slate-200 hover:shadow-sm"
    >
      <!-- Numéro -->
      <span
        class="group-hover:bg-primary-100 flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[10px] font-bold text-slate-400 transition-colors group-hover:text-(--color-primary-600)"
      >
        {{ index + 1 }}
      </span>

      <!-- Icône musique -->
      <Music class="size-4 shrink-0 text-slate-300 group-hover:text-(--color-primary-500)" />

      <!-- Infos chant -->
      <div class="min-w-0 flex-1">
        <p
          class="truncate text-sm font-semibold text-slate-800 group-hover:text-(--color-primary-700)"
        >
          {{ chant.titre }}
        </p>
        <p v-if="chant.artiste" class="truncate text-xs text-slate-400">
          {{ chant.artiste }}
        </p>
      </div>

      <!-- Badge YouTube -->
      <span
        v-if="chant.youtube_url"
        class="flex shrink-0 items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-500"
      >
        <Youtube class="size-3" />
        YT
      </span>

      <!-- Flèche externe -->
      <ExternalLink
        class="size-3.5 shrink-0 text-slate-300 opacity-0 transition-opacity group-hover:opacity-100"
      />
    </RouterLink>
  </div>

  <div
    v-else
    class="flex items-center gap-3 rounded-xl border border-dashed border-slate-200 px-4 py-4 text-sm text-slate-400"
  >
    <Music class="size-4 shrink-0 text-slate-300" />
    <span>Aucun chant dans le répertoire.</span>
  </div>
</template>
