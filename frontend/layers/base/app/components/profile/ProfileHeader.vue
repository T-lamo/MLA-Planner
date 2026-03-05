<script setup lang="ts">
import { Plus } from 'lucide-vue-next'

defineProps<{
  total: number
  isFetching: boolean
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
        {{ isFetching ? 'Chargement...' : `${total} profils au total` }}
      </p>
    </div>
    <button class="btn-primary flex items-center gap-2" @click="$emit('add')">
      <Plus class="size-5" />
      <span>Ajouter un profil</span>
    </button>
  </header>
</template>
