<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import AppSelect from '../ui/AppSelect.vue'

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
      <AppSelect
        :modelValue="activeCampusId"
        :options="campuses.map((c) => ({ label: c.nom, value: c.id }))"
        @update:model-value="emit('update:activeCampusId', $event)"
      />
    </div>
  </div>
</template>
