<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ArrowLeft, Plus, Trash2, ChevronUp, ChevronDown } from 'lucide-vue-next'
import { usePlanningTemplateStore } from '../../../../stores/usePlanningTemplateStore'
import type { PlanningTemplateSlotWrite } from '../../../../types/planning.types'

const route = useRoute()
const templateStore = usePlanningTemplateStore()
const { selectedTemplate, isLoading } = storeToRefs(templateStore)

const templateId = route.params.id as string

interface SlotForm extends PlanningTemplateSlotWrite {
  _tempId: string
}

const form = reactive<{
  nom: string
  description: string
  slots: SlotForm[]
}>({
  nom: '',
  description: '',
  slots: [],
})

const isSaving = ref(false)
const loadError = ref<string | null>(null)

onMounted(async () => {
  try {
    await templateStore.fetchTemplate(templateId)
    const tpl = selectedTemplate.value
    if (tpl) {
      form.nom = tpl.nom
      form.description = tpl.description ?? ''
      form.slots = tpl.slots.map((s) => ({
        _tempId: s.id,
        nom_creneau: s.nom_creneau,
        offset_debut_minutes: s.offset_debut_minutes,
        offset_fin_minutes: s.offset_fin_minutes,
        nb_personnes_requis: s.nb_personnes_requis,
        roles: s.roles.map((r) => r.role_code),
      }))
    }
  } catch {
    loadError.value = 'Impossible de charger ce template.'
  }
})

function addSlot() {
  form.slots.push({
    _tempId: `new-${Date.now()}`,
    nom_creneau: '',
    offset_debut_minutes: 0,
    offset_fin_minutes: 60,
    nb_personnes_requis: 1,
    roles: [],
  })
}

function removeSlot(index: number) {
  form.slots.splice(index, 1)
}

function moveSlot(index: number, direction: 'up' | 'down') {
  const target = direction === 'up' ? index - 1 : index + 1
  if (target < 0 || target >= form.slots.length) return
  const tmp = form.slots[index]!
  form.slots[index] = form.slots[target]!
  form.slots[target] = tmp
}

function addRole(slot: SlotForm) {
  slot.roles.push('')
}

function removeRole(slot: SlotForm, rIdx: number) {
  slot.roles.splice(rIdx, 1)
}

async function handleSave() {
  isSaving.value = true
  try {
    await templateStore.updateTemplate(templateId, {
      nom: form.nom,
      description: form.description || null,
      slots: form.slots.map((s) => ({
        nom_creneau: s.nom_creneau,
        offset_debut_minutes: s.offset_debut_minutes,
        offset_fin_minutes: s.offset_fin_minutes,
        nb_personnes_requis: s.nb_personnes_requis,
        roles: s.roles.filter((r) => r.trim() !== ''),
      })),
    })
    await navigateTo('/planning/templates')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 text-sm text-slate-500">
      <NuxtLink to="/planning/templates" class="flex items-center gap-1 hover:text-slate-700">
        <ArrowLeft class="size-4" />
        <span>Templates</span>
      </NuxtLink>
      <span>/</span>
      <span class="font-medium text-slate-700">Modifier</span>
    </div>

    <!-- Erreur chargement -->
    <div
      v-if="loadError"
      class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
    >
      {{ loadError }}
    </div>

    <!-- Skeleton loading -->
    <div v-else-if="isLoading" class="space-y-4">
      <div class="h-10 animate-pulse rounded-lg bg-slate-100" />
      <div class="h-20 animate-pulse rounded-lg bg-slate-100" />
      <div class="h-32 animate-pulse rounded-lg bg-slate-100" />
    </div>

    <!-- Formulaire -->
    <form v-else class="space-y-6" @submit.prevent="handleSave">
      <!-- Informations générales -->
      <div class="rounded-xl border border-slate-200 bg-white p-6">
        <h2 class="mb-4 text-base font-semibold text-slate-800">Informations générales</h2>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700" for="tpl-nom">
              Nom <span class="text-red-500">*</span>
            </label>
            <input
              id="tpl-nom"
              v-model="form.nom"
              type="text"
              maxlength="100"
              required
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 transition-colors outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              placeholder="Nom du template"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700" for="tpl-desc">
              Description
            </label>
            <textarea
              id="tpl-desc"
              v-model="form.description"
              rows="3"
              class="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 transition-colors outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              placeholder="Description facultative…"
            />
          </div>
        </div>
      </div>

      <!-- Créneaux -->
      <div class="rounded-xl border border-slate-200 bg-white p-6">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-base font-semibold text-slate-800">Créneaux ({{ form.slots.length }})</h2>
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            @click="addSlot"
          >
            <Plus class="size-4" />
            Ajouter
          </button>
        </div>

        <div v-if="form.slots.length === 0" class="py-8 text-center text-sm text-slate-400">
          Aucun créneau — cliquez sur Ajouter pour en créer un.
        </div>

        <div class="space-y-4">
          <div
            v-for="(slot, idx) in form.slots"
            :key="slot._tempId"
            class="rounded-lg border border-slate-200 bg-slate-50 p-4"
          >
            <!-- En-tête créneau -->
            <div class="mb-3 flex items-center justify-between">
              <span class="text-xs font-semibold tracking-wider text-slate-400 uppercase">
                Créneau {{ idx + 1 }}
              </span>
              <div class="flex items-center gap-1">
                <button
                  type="button"
                  :disabled="idx === 0"
                  class="rounded p-1 text-slate-400 transition-colors hover:bg-slate-200 disabled:opacity-30"
                  @click="moveSlot(idx, 'up')"
                >
                  <ChevronUp class="size-4" />
                </button>
                <button
                  type="button"
                  :disabled="idx === form.slots.length - 1"
                  class="rounded p-1 text-slate-400 transition-colors hover:bg-slate-200 disabled:opacity-30"
                  @click="moveSlot(idx, 'down')"
                >
                  <ChevronDown class="size-4" />
                </button>
                <button
                  type="button"
                  class="rounded p-1 text-slate-400 transition-colors hover:bg-red-100 hover:text-red-600"
                  @click="removeSlot(idx)"
                >
                  <Trash2 class="size-4" />
                </button>
              </div>
            </div>

            <div class="grid gap-3 sm:grid-cols-2">
              <!-- Nom -->
              <div class="sm:col-span-2">
                <label class="mb-1 block text-xs font-medium text-slate-600">
                  Nom du créneau
                </label>
                <input
                  v-model="slot.nom_creneau"
                  type="text"
                  maxlength="100"
                  required
                  class="w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
                  placeholder="Ex : Louange Matin"
                />
              </div>
              <!-- Offset début -->
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-600">
                  Début (min depuis début activité)
                </label>
                <input
                  v-model.number="slot.offset_debut_minutes"
                  type="number"
                  min="0"
                  class="w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
                />
              </div>
              <!-- Offset fin -->
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-600">
                  Fin (min depuis début activité)
                </label>
                <input
                  v-model.number="slot.offset_fin_minutes"
                  type="number"
                  min="1"
                  class="w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
                />
              </div>
              <!-- Nb personnes -->
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-600">
                  Personnes requises
                </label>
                <input
                  v-model.number="slot.nb_personnes_requis"
                  type="number"
                  min="1"
                  class="w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
                />
              </div>
            </div>

            <!-- Rôles -->
            <div class="mt-3">
              <div class="mb-1 flex items-center justify-between">
                <label class="text-xs font-medium text-slate-600">Rôles requis</label>
                <button
                  type="button"
                  class="text-xs font-medium text-blue-600 hover:underline"
                  @click="addRole(slot)"
                >
                  + Ajouter
                </button>
              </div>
              <div class="flex flex-wrap gap-2">
                <div v-for="(_, rIdx) in slot.roles" :key="rIdx" class="flex items-center gap-1">
                  <input
                    v-model="slot.roles[rIdx]"
                    type="text"
                    class="w-28 rounded border border-slate-300 px-2 py-1 text-xs uppercase outline-none focus:border-blue-400"
                    placeholder="ROLE_CODE"
                  />
                  <button
                    type="button"
                    class="text-slate-400 hover:text-red-500"
                    @click="removeRole(slot, rIdx)"
                  >
                    <Trash2 class="size-3.5" />
                  </button>
                </div>
                <span v-if="slot.roles.length === 0" class="text-xs text-slate-400 italic">
                  Aucun rôle
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-3">
        <NuxtLink
          to="/planning/templates"
          class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
        >
          Annuler
        </NuxtLink>
        <button
          type="submit"
          :disabled="isSaving || !form.nom.trim()"
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
        >
          {{ isSaving ? 'Sauvegarde…' : 'Sauvegarder' }}
        </button>
      </div>
    </form>
  </div>
</template>
