<script setup lang="ts">
import { ref, watch } from 'vue'
import { Plus, User } from 'lucide-vue-next'
import AppDrawer from '~~/layers/base/app/components/AppDrawer.vue'

const props = defineProps<{ isOpen: boolean }>()
const emit = defineEmits<{
  close: []
  created: [name: string]
}>()

const nom = ref('')
const nomError = ref('')

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      nom.value = ''
      nomError.value = ''
    }
  },
)

function handleSave(): void {
  nomError.value = ''
  const trimmed = nom.value.trim()
  if (!trimmed) {
    nomError.value = 'Nom requis'
    return
  }
  emit('created', trimmed)
  emit('close')
}
</script>

<template>
  <AppDrawer :isOpen="isOpen" title="Nouvel artiste" @close="emit('close')">
    <div class="space-y-5">
      <div class="flex items-center gap-3 rounded-xl bg-(--color-primary-50) px-4 py-3">
        <User class="size-5 shrink-0 text-(--color-primary-500)" />
        <p class="text-sm text-(--color-primary-700)">
          Saisissez le nom de l'artiste ou du groupe à associer à ce chant.
        </p>
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
          Nom <span class="text-(--color-red-500)">*</span>
        </label>
        <input
          v-model="nom"
          type="text"
          placeholder="Ex : Hillsong, ICC Worship, Maverick City…"
          class="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none"
          :class="
            nomError
              ? 'border-(--color-red-400) focus:border-(--color-red-400)'
              : 'border-(--color-neutral-300) focus:border-(--color-primary-400)'
          "
          @keyup.enter="handleSave"
        />
        <p v-if="nomError" class="mt-1 text-xs text-(--color-red-500)">{{ nomError }}</p>
      </div>
    </div>

    <template #footer>
      <div class="flex gap-3">
        <button type="button" class="btn btn-secondary flex-1" @click="emit('close')">
          Annuler
        </button>
        <button type="button" class="btn btn-primary flex-1" @click="handleSave">
          <Plus class="size-4" />
          Ajouter
        </button>
      </div>
    </template>
  </AppDrawer>
</template>
