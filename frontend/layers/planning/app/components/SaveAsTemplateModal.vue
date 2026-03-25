<template>
  <Teleport to="body">
    <Transition
      enterActiveClass="transition-opacity duration-200"
      enterFromClass="opacity-0"
      enterToClass="opacity-100"
      leaveActiveClass="transition-opacity duration-150"
      leaveFromClass="opacity-100"
      leaveToClass="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[20000] flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-slate-900/40" @click="handleClose" />

        <!-- Panel -->
        <div class="relative w-full max-w-md rounded-2xl bg-white shadow-2xl" @click.stop>
          <!-- Header -->
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
            <div class="flex items-center gap-3">
              <div class="flex size-9 items-center justify-center rounded-full bg-indigo-50">
                <BookmarkPlus class="size-5 text-indigo-600" />
              </div>
              <h2 id="modal-title" class="text-base font-bold text-slate-800">
                Sauvegarder comme template
              </h2>
            </div>
            <button
              class="rounded-full p-2 text-slate-400 transition-colors hover:bg-slate-100"
              @click="handleClose"
            >
              <X class="size-4" />
            </button>
          </div>

          <!-- Body -->
          <div class="space-y-4 px-6 py-5">
            <p class="text-sm text-slate-500">
              Ce planning sera sauvegardé comme template réutilisable. Les créneaux et rôles seront
              conservés ; les membres affectés ne seront pas inclus.
            </p>

            <!-- Nom -->
            <div>
              <label for="template-nom" class="mb-1.5 block text-xs font-semibold text-slate-700">
                Nom du template <span class="text-red-500">*</span>
              </label>
              <input
                id="template-nom"
                v-model="nom"
                type="text"
                maxlength="150"
                placeholder="Ex : Culte dominical standard"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800 transition-colors outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                :class="{ 'border-red-300 focus:border-red-400 focus:ring-red-100': nomError }"
                @input="nomError = ''"
              />
              <p v-if="nomError" class="mt-1 text-xs text-red-500">{{ nomError }}</p>
            </div>

            <!-- Description -->
            <div>
              <label for="template-desc" class="mb-1.5 block text-xs font-semibold text-slate-700">
                Description
                <span class="ml-1 font-normal text-slate-400">(optionnel)</span>
              </label>
              <textarea
                id="template-desc"
                v-model="description"
                rows="3"
                maxlength="500"
                placeholder="Décrivez l'usage de ce template…"
                class="w-full resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800 transition-colors outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
              />
            </div>

            <!-- Visibilité -->
            <div>
              <label
                for="template-visibilite"
                class="mb-1.5 block text-xs font-semibold text-slate-700"
              >
                Visibilité
              </label>
              <select
                id="template-visibilite"
                v-model="visibilite"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
              >
                <option value="MINISTERE">Ministère — tous les membres du ministère</option>
                <option value="CAMPUS">Campus — tous les campus</option>
                <option value="PRIVE">Privé — visible par moi uniquement</option>
              </select>
            </div>

            <!-- Erreur API -->
            <p v-if="templateError" class="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
              {{ templateError }}
            </p>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <button
              type="button"
              class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50"
              :disabled="isSaving"
              @click="handleClose"
            >
              Annuler
            </button>
            <button
              type="button"
              class="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="isSaving || !nom.trim()"
              @click="handleSave"
            >
              <Loader2 v-if="isSaving" class="size-4 animate-spin" />
              <BookmarkPlus v-else class="size-4" />
              Sauvegarder
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { BookmarkPlus, Loader2, X } from 'lucide-vue-next'
import { usePlanningTemplates } from '../composables/usePlanningTemplates'
import type { PlanningTemplateRead, VisibiliteTemplate } from '../types/planning.types'

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------
const props = defineProps<{
  isOpen: boolean
  planningId: string
}>()

const emit = defineEmits<{
  close: []
  saved: [template: PlanningTemplateRead]
}>()

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const nom = ref('')
const description = ref('')
const visibilite = ref<VisibiliteTemplate>('MINISTERE')
const nomError = ref('')

const { isSaving, templateError, saveAsTemplate } = usePlanningTemplates()

// Réinitialise le formulaire à chaque ouverture
watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      nom.value = ''
      description.value = ''
      visibilite.value = 'MINISTERE'
      nomError.value = ''
    }
  },
)

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------
function handleClose(): void {
  if (isSaving.value) return
  emit('close')
}

async function handleSave(): Promise<void> {
  const trimmed = nom.value.trim()
  if (!trimmed) {
    nomError.value = 'Le nom du template est obligatoire.'
    return
  }

  const result = await saveAsTemplate(props.planningId, {
    nom: trimmed,
    description: description.value.trim() || null,
    visibilite: visibilite.value,
  })

  if (result) {
    emit('saved', result)
    emit('close')
  }
}
</script>
