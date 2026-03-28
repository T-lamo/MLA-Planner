<script setup lang="ts">
import { ref, watch } from 'vue'
import { Plus, Tag } from 'lucide-vue-next'
import AppDrawer from '~~/layers/base/app/components/AppDrawer.vue'

const props = defineProps<{ isOpen: boolean }>()
const emit = defineEmits<{
  close: []
  created: [code: string]
}>()

const { createCategorie } = useSongbook()

const libelle = ref('')
const code = ref('')
const isSaving = ref(false)
const apiError = ref('')
const libelleError = ref('')
const codeError = ref('')

watch(libelle, (val) => {
  code.value = val
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
})

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      libelle.value = ''
      code.value = ''
      apiError.value = ''
      libelleError.value = ''
      codeError.value = ''
    }
  },
)

async function handleSave(): Promise<void> {
  libelleError.value = ''
  codeError.value = ''
  apiError.value = ''

  const trimCode = code.value.trim()
  const trimLibelle = libelle.value.trim()

  if (!trimLibelle) {
    libelleError.value = 'Libellé requis'
    return
  }
  if (!trimCode) {
    codeError.value = 'Code requis'
    return
  }

  isSaving.value = true
  try {
    await createCategorie({ code: trimCode, libelle: trimLibelle })
    emit('created', trimCode)
    emit('close')
  } catch (e: unknown) {
    const err = e as { data?: { error?: { message?: string } } }
    apiError.value = err?.data?.error?.message ?? 'Erreur lors de la création'
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <AppDrawer :isOpen="isOpen" title="Nouvelle catégorie" @close="emit('close')">
    <div class="space-y-5">
      <div class="flex items-center gap-3 rounded-xl bg-(--color-primary-50) px-4 py-3">
        <Tag class="size-5 shrink-0 text-(--color-primary-500)" />
        <p class="text-sm text-(--color-primary-700)">
          Les catégories permettent de classer vos chants par thème ou style.
        </p>
      </div>

      <!-- Libellé -->
      <div>
        <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
          Libellé <span class="text-(--color-red-500)">*</span>
        </label>
        <input
          v-model="libelle"
          type="text"
          placeholder="Ex : Louange, Adoration, Gospel…"
          class="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none"
          :class="
            libelleError
              ? 'border-(--color-red-400) focus:border-(--color-red-400)'
              : 'border-(--color-neutral-300) focus:border-(--color-primary-400)'
          "
          @keyup.enter="handleSave"
        />
        <p v-if="libelleError" class="mt-1 text-xs text-(--color-red-500)">{{ libelleError }}</p>
      </div>

      <!-- Code -->
      <div>
        <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
          Code <span class="text-(--color-red-500)">*</span>
        </label>
        <input
          v-model="code"
          type="text"
          placeholder="Ex : LOUANGE"
          class="w-full rounded-lg border px-3 py-2 font-mono text-sm tracking-wider uppercase focus:outline-none"
          :class="
            codeError
              ? 'border-(--color-red-400) focus:border-(--color-red-400)'
              : 'border-(--color-neutral-300) focus:border-(--color-primary-400)'
          "
          @keyup.enter="handleSave"
        />
        <p class="mt-1 text-xs text-(--color-neutral-400)">
          Généré automatiquement depuis le libellé · modifiable
        </p>
        <p v-if="codeError" class="mt-0.5 text-xs text-(--color-red-500)">{{ codeError }}</p>
      </div>

      <p
        v-if="apiError"
        class="rounded-lg bg-(--color-red-50) px-3 py-2 text-sm text-(--color-red-600)"
      >
        {{ apiError }}
      </p>
    </div>

    <template #footer>
      <div class="flex gap-3">
        <button type="button" class="btn btn-secondary flex-1" @click="emit('close')">
          Annuler
        </button>
        <button
          type="button"
          class="btn btn-primary flex-1"
          :disabled="isSaving"
          @click="handleSave"
        >
          <Plus class="size-4" />
          Créer la catégorie
        </button>
      </div>
    </template>
  </AppDrawer>
</template>
