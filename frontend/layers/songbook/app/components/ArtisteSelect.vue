<script setup lang="ts">
import { computed, ref } from 'vue'
import { Plus } from 'lucide-vue-next'
import AppSearchSelect from '~~/layers/base/app/components/ui/AppSearchSelect.vue'
import ArtisteDrawer from './ArtisteDrawer.vue'

const props = defineProps<{
  modelValue: string
  suggestions: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const showDrawer = ref(false)

const options = computed(() => props.suggestions.map((a) => ({ label: a, value: a })))

function onCreated(name: string): void {
  emit('update:modelValue', name)
}
</script>

<template>
  <div class="flex gap-2">
    <div class="flex-1">
      <AppSearchSelect
        :modelValue="modelValue"
        :options="options"
        placeholder="Rechercher…"
        @update:model-value="emit('update:modelValue', $event)"
      />
    </div>
    <button
      type="button"
      class="border-primary-200 text-primary-600 hover:bg-primary-50 inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-sm"
      title="Ajouter un nouvel artiste"
      @click="showDrawer = true"
    >
      <Plus class="h-4 w-4" />
      Nouveau
    </button>
  </div>

  <ArtisteDrawer :isOpen="showDrawer" @close="showDrawer = false" @created="onCreated" />
</template>
