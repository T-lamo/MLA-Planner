<script setup lang="ts">
import { Plus, X } from 'lucide-vue-next'
import type { ChantCategorieRead } from '../types/chant'

const props = defineProps<{
  modelValue: string
  categories: ChantCategorieRead[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { createCategorie } = useSongbook()

// ── Formulaire inline de création ─────────────────────────────────────────
const showCreate = ref(false)
const newCode = ref('')
const newLibelle = ref('')
const isSaving = ref(false)
const codeError = ref('')
const libelleError = ref('')

function openCreate() {
  newCode.value = ''
  newLibelle.value = ''
  codeError.value = ''
  libelleError.value = ''
  showCreate.value = true
}

function cancelCreate() {
  showCreate.value = false
}

async function handleCreate() {
  codeError.value = ''
  libelleError.value = ''

  const code = newCode.value.trim().toUpperCase().replace(/\s+/g, '_')
  const libelle = newLibelle.value.trim()

  if (!code) {
    codeError.value = 'Code requis'
    return
  }
  if (!libelle) {
    libelleError.value = 'Libellé requis'
    return
  }
  if (props.categories.some((c) => c.code === code)) {
    codeError.value = 'Ce code existe déjà'
    return
  }

  isSaving.value = true
  try {
    await createCategorie({ code, libelle })
    emit('update:modelValue', code)
    showCreate.value = false
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-2">
    <!-- Sélecteur existant -->
    <div v-if="!showCreate" class="flex gap-2">
      <select
        :value="modelValue"
        class="flex-1 rounded-lg border border-(--color-neutral-300) px-3 py-2 text-sm focus:border-(--color-primary-400) focus:outline-none"
        @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">— Aucune —</option>
        <option v-for="cat in categories" :key="cat.code" :value="cat.code">
          {{ cat.libelle }}
        </option>
      </select>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg border border-(--color-primary-200) px-3 py-2 text-sm text-(--color-primary-600) hover:bg-(--color-primary-50)"
        title="Créer une nouvelle catégorie"
        @click="openCreate"
      >
        <Plus class="h-4 w-4" />
        Nouvelle
      </button>
    </div>

    <!-- Formulaire de création inline -->
    <div
      v-else
      class="space-y-3 rounded-xl border border-(--color-primary-200) bg-(--color-primary-50) p-4"
    >
      <div class="flex items-center justify-between">
        <p class="text-sm font-medium text-(--color-primary-700)">Nouvelle catégorie</p>
        <button
          type="button"
          class="rounded p-0.5 text-(--color-neutral-400) hover:text-(--color-neutral-600)"
          @click="cancelCreate"
        >
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-(--color-neutral-600)">
            Code <span class="text-(--color-red-500)">*</span>
          </label>
          <input
            v-model="newCode"
            type="text"
            placeholder="Ex : LOUANGE"
            class="w-full rounded-lg border px-3 py-1.5 text-sm uppercase focus:outline-none"
            :class="
              codeError
                ? 'border-(--color-red-400) focus:border-(--color-red-400)'
                : 'border-(--color-neutral-300) focus:border-(--color-primary-400)'
            "
            @keyup.enter="handleCreate"
          />
          <p v-if="codeError" class="mt-0.5 text-xs text-(--color-red-500)">{{ codeError }}</p>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-(--color-neutral-600)">
            Libellé <span class="text-(--color-red-500)">*</span>
          </label>
          <input
            v-model="newLibelle"
            type="text"
            placeholder="Ex : Louange"
            class="w-full rounded-lg border px-3 py-1.5 text-sm focus:outline-none"
            :class="
              libelleError
                ? 'border-(--color-red-400) focus:border-(--color-red-400)'
                : 'border-(--color-neutral-300) focus:border-(--color-primary-400)'
            "
            @keyup.enter="handleCreate"
          />
          <p v-if="libelleError" class="mt-0.5 text-xs text-(--color-red-500)">
            {{ libelleError }}
          </p>
        </div>
      </div>

      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="rounded-lg px-3 py-1.5 text-sm text-(--color-neutral-600) hover:bg-(--color-neutral-100)"
          @click="cancelCreate"
        >
          Annuler
        </button>
        <button
          type="button"
          :disabled="isSaving"
          class="inline-flex items-center gap-1.5 rounded-lg bg-(--color-primary-600) px-3 py-1.5 text-sm font-medium text-white hover:bg-(--color-primary-700) disabled:opacity-50"
          @click="handleCreate"
        >
          <Plus class="h-3.5 w-3.5" />
          Créer
        </button>
      </div>
    </div>
  </div>
</template>
