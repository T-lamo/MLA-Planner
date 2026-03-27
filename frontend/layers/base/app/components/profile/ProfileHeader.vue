<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import CanGuard from '../ui/CanGuard.vue'

defineProps<{
  total: number
  isFetching: boolean
  contextLabel?: string
}>()

defineEmits<{
  (e: 'add'): void
}>()
</script>

<template>
  <header class="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Gestion des Profils</h1>
      <p class="text-sm text-slate-500">
        <template v-if="isFetching">Chargement…</template>
        <template v-else>
          {{ total }} membre{{ total !== 1 ? 's' : '' }}
          <span v-if="contextLabel"> · {{ contextLabel }}</span>
        </template>
      </p>
    </div>
    <CanGuard capability="MEMBRE_CREATE">
      <button class="btn btn-primary" @click="$emit('add')">
        <Plus class="size-5" />
        <span>Ajouter un profil</span>
      </button>
    </CanGuard>
  </header>
</template>
