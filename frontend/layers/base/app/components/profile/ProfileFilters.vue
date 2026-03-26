<script setup lang="ts">
import { Search } from 'lucide-vue-next'

const _props = defineProps<{
  searchQuery: string
  activeCampusId: string
  campuses: Array<{ id: string; nom: string }>
}>()

const emit = defineEmits(['update:searchQuery', 'update:activeCampusId'])
</script>

<template>
  <div
    class="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:flex-row md:items-center"
  >
    <div class="relative flex-1">
      <Search class="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
      <input
        :value="searchQuery"
        type="text"
        placeholder="Rechercher par nom, email..."
        class="form-input w-full bg-white pl-10"
        @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="flex items-center gap-3">
      <span class="text-xs font-bold tracking-wider text-slate-400 uppercase">Campus</span>
      <select
        :value="activeCampusId"
        class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-(--color-primary-600) focus:outline-hidden"
        @change="emit('update:activeCampusId', ($event.target as HTMLSelectElement).value)"
      >
        <option v-for="c in campuses" :key="c.id" :value="c.id">{{ c.nom }}</option>
      </select>
    </div>
  </div>
</template>
