<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Plus, Trash2, ChevronUp, ChevronDown } from 'lucide-vue-next'
import { usePlanningTemplateStore } from '../stores/usePlanningTemplateStore'
import type { PlanningTemplateSlotWrite } from '../types/planning.types'

const props = defineProps<{
  templateId: string | null
}>()

const emit = defineEmits<{
  (e: 'close' | 'saved'): void
}>()

const templateStore = usePlanningTemplateStore()
const { selectedTemplate, isLoading } = storeToRefs(templateStore)

interface SlotForm extends PlanningTemplateSlotWrite {
  _tempId: string
}

const form = reactive<{
  nom: string
  description: string
  slots: SlotForm[]
}>({ nom: '', description: '', slots: [] })

const isSaving = ref(false)
const loadError = ref<string | null>(null)

function populateForm() {
  const tpl = selectedTemplate.value
  if (!tpl) return
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

watch(
  () => props.templateId,
  async (id) => {
    if (!id) return
    loadError.value = null
    try {
      await templateStore.fetchTemplate(id)
      populateForm()
    } catch {
      loadError.value = 'Impossible de charger ce template.'
    }
  },
  { immediate: true },
)

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
  if (!props.templateId) return
  isSaving.value = true
  try {
    await templateStore.updateTemplate(props.templateId, {
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
    emit('saved')
    emit('close')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <AppDrawer
    :isOpen="templateId !== null"
    :title="form.nom || 'Modifier le template'"
    initialSize="half"
    @close="emit('close')"
  >
    <!-- Corps -->
    <div class="space-y-6">
      <!-- Erreur chargement -->
      <div
        v-if="loadError"
        class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        {{ loadError }}
      </div>

      <!-- Skeleton -->
      <div v-else-if="isLoading" class="space-y-4">
        <div class="h-10 animate-pulse rounded-lg bg-slate-100" />
        <div class="h-20 animate-pulse rounded-lg bg-slate-100" />
        <div class="h-32 animate-pulse rounded-lg bg-slate-100" />
      </div>

      <!-- Formulaire -->
      <form v-else id="template-edit-form" class="space-y-6" @submit.prevent="handleSave">
        <!-- Infos générales -->
        <div class="rounded-xl border border-slate-200 bg-white p-5">
          <h3 class="mb-4 text-sm font-semibold tracking-wide text-slate-700 uppercase">
            Informations générales
          </h3>
          <div class="space-y-4">
            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700" for="drawer-tpl-nom">
                Nom <span class="text-red-500">*</span>
              </label>
              <input
                id="drawer-tpl-nom"
                v-model="form.nom"
                type="text"
                maxlength="100"
                required
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 transition-colors outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                placeholder="Nom du template"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700" for="drawer-tpl-desc">
                Description
              </label>
              <textarea
                id="drawer-tpl-desc"
                v-model="form.description"
                rows="3"
                class="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 transition-colors outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                placeholder="Description facultative…"
              />
            </div>
          </div>
        </div>

        <!-- Créneaux -->
        <div class="rounded-xl border border-slate-200 bg-white p-5">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-sm font-semibold tracking-wide text-slate-700 uppercase">
              Créneaux ({{ form.slots.length }})
            </h3>
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-lg bg-(--color-primary-600) px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-700)"
              @click="addSlot"
            >
              <Plus class="size-4" />
              Ajouter
            </button>
          </div>

          <p v-if="form.slots.length === 0" class="py-6 text-center text-sm text-slate-400">
            Aucun créneau — cliquez sur Ajouter pour en créer un.
          </p>

          <div class="space-y-4">
            <div
              v-for="(slot, idx) in form.slots"
              :key="slot._tempId"
              class="rounded-lg border border-slate-200 bg-slate-50 p-4"
            >
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
                <div>
                  <label class="mb-1 block text-xs font-medium text-slate-600"> Début (min) </label>
                  <input
                    v-model.number="slot.offset_debut_minutes"
                    type="number"
                    min="0"
                    class="w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
                  />
                </div>
                <div>
                  <label class="mb-1 block text-xs font-medium text-slate-600"> Fin (min) </label>
                  <input
                    v-model.number="slot.offset_fin_minutes"
                    type="number"
                    min="1"
                    class="w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
                  />
                </div>
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
                    class="text-xs font-medium text-(--color-primary-600) hover:underline"
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
      </form>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex justify-end gap-3">
        <button
          type="button"
          class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          @click="emit('close')"
        >
          Annuler
        </button>
        <button
          type="submit"
          form="template-edit-form"
          :disabled="isSaving || !form.nom.trim()"
          class="rounded-lg bg-(--color-primary-600) px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-700) disabled:opacity-50"
        >
          {{ isSaving ? 'Sauvegarde…' : 'Sauvegarder' }}
        </button>
      </div>
    </template>
  </AppDrawer>
</template>
