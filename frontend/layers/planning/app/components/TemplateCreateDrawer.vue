<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Plus, Trash2, ChevronUp, ChevronDown } from 'lucide-vue-next'
import { usePlanningTemplateStore } from '../stores/usePlanningTemplateStore'
import { PlanningRepository } from '../repositories/PlanningRepository'
import type {
  PlanningTemplateSlotWrite,
  RoleCompetenceRead,
  VisibiliteTemplate,
} from '../types/planning.types'

const props = defineProps<{ isOpen: boolean }>()

const emit = defineEmits<{
  (e: 'close' | 'created'): void
}>()

const templateStore = usePlanningTemplateStore()
const repo = new PlanningRepository()

interface SlotForm extends PlanningTemplateSlotWrite {
  _tempId: string
}

const form = reactive<{
  nom: string
  description: string
  activite_type: string
  duree_minutes: number
  visibilite: VisibiliteTemplate
  slots: SlotForm[]
}>({
  nom: '',
  description: '',
  activite_type: '',
  duree_minutes: 120,
  visibilite: 'MINISTERE',
  slots: [],
})

const isSaving = ref(false)
const rolesCompetences = ref<RoleCompetenceRead[]>([])

function resetForm() {
  form.nom = ''
  form.description = ''
  form.activite_type = ''
  form.duree_minutes = 120
  form.visibilite = 'MINISTERE'
  form.slots = []
}

watch(
  () => props.isOpen,
  async (open) => {
    if (!open) return
    resetForm()
    if (rolesCompetences.value.length === 0) {
      try {
        rolesCompetences.value = await repo.getRoleCompetences()
      } catch {
        rolesCompetences.value = []
      }
    }
  },
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
  slot.roles.push({ role_code: '', membres_suggeres_ids: [] })
}

function removeRole(slot: SlotForm, rIdx: number) {
  slot.roles.splice(rIdx, 1)
}

async function handleSave() {
  isSaving.value = true
  try {
    await templateStore.createTemplate({
      nom: form.nom,
      description: form.description || null,
      activite_type: form.activite_type || null,
      duree_minutes: form.duree_minutes,
      visibilite: form.visibilite,
      slots: form.slots.map((s) => ({
        nom_creneau: s.nom_creneau,
        offset_debut_minutes: s.offset_debut_minutes,
        offset_fin_minutes: s.offset_fin_minutes,
        nb_personnes_requis: s.nb_personnes_requis,
        roles: s.roles.filter((r) => r.role_code.trim() !== ''),
      })),
    })
    emit('created')
    emit('close')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <AppDrawer
    :isOpen="isOpen"
    title="Nouveau template"
    initialSize="standard"
    @close="emit('close')"
  >
    <form id="template-create-form" class="space-y-6" @submit.prevent="handleSave">
      <!-- Informations générales -->
      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-semibold tracking-wide text-slate-700 uppercase">
          Informations générales
        </h3>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700" for="create-tpl-nom">
              Nom <span class="text-red-500">*</span>
            </label>
            <input
              id="create-tpl-nom"
              v-model="form.nom"
              type="text"
              maxlength="100"
              required
              class="form-input"
              placeholder="Nom du template"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700" for="create-tpl-desc">
              Description
            </label>
            <textarea
              id="create-tpl-desc"
              v-model="form.description"
              rows="3"
              class="form-input resize-none"
              placeholder="Description facultative…"
            />
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700" for="create-tpl-type">
                Type d'activité
              </label>
              <input
                id="create-tpl-type"
                v-model="form.activite_type"
                type="text"
                maxlength="100"
                class="form-input"
                placeholder="Ex : Culte Dominical"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700" for="create-tpl-duree">
                Durée (minutes)
              </label>
              <input
                id="create-tpl-duree"
                v-model.number="form.duree_minutes"
                type="number"
                min="1"
                class="form-input"
              />
            </div>
          </div>
          <div>
            <label
              class="mb-1 block text-sm font-medium text-slate-700"
              for="create-tpl-visibilite"
            >
              Visibilité
            </label>
            <div class="form-select-wrapper">
              <select
                id="create-tpl-visibilite"
                v-model="form.visibilite"
                class="form-input form-select"
              >
                <option value="PRIVE">Privé — visible par moi uniquement</option>
                <option value="MINISTERE">Ministère — tous les membres du ministère</option>
                <option value="CAMPUS">Campus — tous les campus</option>
              </select>
              <svg
                class="form-select-chevron"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M3 5l4 4 4-4" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Créneaux -->
      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-sm font-semibold tracking-wide text-slate-700 uppercase">
            Créneaux ({{ form.slots.length }})
          </h3>
          <button type="button" class="btn btn-primary btn-sm" @click="addSlot">
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
                <label class="mb-1 block text-xs font-medium text-slate-600">Nom du créneau</label>
                <input
                  v-model="slot.nom_creneau"
                  type="text"
                  maxlength="100"
                  required
                  class="form-input form-input-sm"
                  placeholder="Ex : Louange Matin"
                />
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-600">Début (min)</label>
                <input
                  v-model.number="slot.offset_debut_minutes"
                  type="number"
                  min="0"
                  class="form-input form-input-sm"
                />
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-600">Fin (min)</label>
                <input
                  v-model.number="slot.offset_fin_minutes"
                  type="number"
                  min="1"
                  class="form-input form-input-sm"
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
                  class="form-input form-input-sm"
                />
              </div>
            </div>

            <!-- Rôles -->
            <div class="mt-3 space-y-3">
              <div class="flex items-center justify-between">
                <label class="text-xs font-medium text-slate-600">Rôles requis</label>
                <button
                  type="button"
                  class="text-xs font-medium text-(--color-primary-600) hover:underline"
                  @click="addRole(slot)"
                >
                  + Ajouter
                </button>
              </div>

              <p v-if="slot.roles.length === 0" class="text-xs text-slate-400 italic">Aucun rôle</p>

              <div
                v-for="(role, rIdx) in slot.roles"
                :key="rIdx"
                class="rounded-md border border-slate-200 bg-white p-3"
              >
                <div class="flex items-center gap-2">
                  <div class="form-select-wrapper flex-1">
                    <select v-model="role.role_code" class="form-input form-input-sm form-select">
                      <option value="">— Choisir un rôle —</option>
                      <option v-for="rc in rolesCompetences" :key="rc.code" :value="rc.code">
                        {{ rc.libelle }}
                      </option>
                    </select>
                    <svg
                      class="form-select-chevron"
                      viewBox="0 0 14 14"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M3 5l4 4 4-4" />
                    </svg>
                  </div>
                  <button
                    type="button"
                    class="shrink-0 text-slate-400 hover:text-red-500"
                    @click="removeRole(slot, rIdx)"
                  >
                    <Trash2 class="size-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </form>

    <template #footer>
      <div class="flex justify-end gap-3">
        <button type="button" class="btn btn-secondary" @click="emit('close')">Annuler</button>
        <button
          type="submit"
          form="template-create-form"
          :disabled="isSaving || !form.nom.trim()"
          class="btn btn-primary"
        >
          {{ isSaving ? 'Création…' : 'Créer le template' }}
        </button>
      </div>
    </template>
  </AppDrawer>
</template>
