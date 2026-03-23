<script setup lang="ts">
import { Music, User, Tag } from 'lucide-vue-next'
import type { ChantRead, ChantCategorieRead } from '../types/chant'

defineProps<{
  chant: ChantRead
  categorie?: ChantCategorieRead
  selected?: boolean
}>()

const emit = defineEmits<{
  select: [id: string]
}>()
</script>

<template>
  <button
    type="button"
    class="w-full rounded-lg border px-4 py-3 text-left transition-colors"
    :class="[
      selected
        ? 'border-(--color-primary-500) bg-(--color-primary-50)'
        : 'border-(--color-neutral-200) bg-white hover:border-(--color-primary-300) hover:bg-(--color-neutral-50)',
    ]"
    @click="emit('select', chant.id)"
  >
    <div class="flex items-start gap-3">
      <Music class="mt-0.5 h-4 w-4 shrink-0 text-(--color-primary-500)" />
      <div class="min-w-0 flex-1">
        <p class="truncate font-medium text-(--color-neutral-900)">{{ chant.titre }}</p>
        <div
          class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-(--color-neutral-500)"
        >
          <span v-if="chant.artiste" class="flex items-center gap-1">
            <User class="h-3 w-3" />
            {{ chant.artiste }}
          </span>
          <span v-if="categorie" class="flex items-center gap-1">
            <Tag class="h-3 w-3" />
            {{ categorie.libelle }}
          </span>
        </div>
      </div>
    </div>
  </button>
</template>
