<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ArrowLeft, Plus, Trash2, ChevronUp, ChevronDown } from 'lucide-vue-next'
import { usePlanningTemplateStore } from '../../../../stores/usePlanningTemplateStore'
import { PlanningRepository } from '../../../../repositories/PlanningRepository'
import type {
  MembreSimple,
  PlanningTemplateSlotWrite,
  TemplateRoleWrite,
} from '../../../../types/planning.types'

const route = useRoute()
const templateStore = usePlanningTemplateStore()
const { selectedTemplate, isLoading } = storeToRefs(templateStore)
const repo = new PlanningRepository()

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
const membresDisponibles = ref<MembreSimple[]>([])

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
        roles: s.roles.map(
          (r): TemplateRoleWrite => ({
            role_code: r.role_code,
            membres_suggeres_ids: r.membres_suggeres.map((m) => m.membre_id),
          }),
        ),
      }))
      if (tpl.ministere_id) {
        try {
          membresDisponibles.value = await repo.getMembersByMinistere(tpl.ministere_id)
        } catch {
          membresDisponibles.value = []
        }
      }
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
  slot.roles.push({ role_code: '', membres_suggeres_ids: [] })
}

function removeRole(slot: SlotForm, rIdx: number) {
  slot.roles.splice(rIdx, 1)
}

function addSuggestedMember(role: TemplateRoleWrite, membreId: string) {
  if (!role.membres_suggeres_ids.includes(membreId)) {
    role.membres_suggeres_ids.push(membreId)
  }
}

function removeSuggestedMember(role: TemplateRoleWrite, membreId: string) {
  const idx = role.membres_suggeres_ids.indexOf(membreId)
  if (idx !== -1) role.membres_suggeres_ids.splice(idx, 1)
}

function membreLabel(id: string): string {
  const m = membresDisponibles.value.find((x) => x.id === id)
  return m ? `${m.prenom} ${m.nom}` : id
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
        roles: s.roles.filter((r) => r.role_code.trim() !== ''),
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
              class="form-input"
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
              class="form-input resize-none"
              placeholder="Description facultative…"
            />
          </div>
        </div>
      </div>

      <!-- Créneaux -->
      <div class="rounded-xl border border-slate-200 bg-white p-6">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-base font-semibold text-slate-800">Créneaux ({{ form.slots.length }})</h2>
          <button type="button" class="btn btn-primary btn-sm" @click="addSlot">
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
                  class="form-input form-input-sm"
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
                  class="form-input form-input-sm"
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
                  class="form-input form-input-sm"
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
                  class="text-xs font-medium text-blue-600 hover:underline"
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
                <!-- Code rôle + supprimer -->
                <div class="mb-2 flex items-center gap-2">
                  <input
                    v-model="role.role_code"
                    type="text"
                    class="form-input form-input-sm w-32 uppercase"
                    placeholder="ROLE_CODE"
                  />
                  <button
                    type="button"
                    class="ml-auto text-slate-400 hover:text-red-500"
                    @click="removeRole(slot, rIdx)"
                  >
                    <Trash2 class="size-3.5" />
                  </button>
                </div>

                <!-- Membres suggérés -->
                <div class="space-y-1.5">
                  <p class="text-xs font-medium text-slate-500">Membres suggérés</p>

                  <!-- Tags membres déjà ajoutés -->
                  <div v-if="role.membres_suggeres_ids.length > 0" class="flex flex-wrap gap-1">
                    <span
                      v-for="membreId in role.membres_suggeres_ids"
                      :key="membreId"
                      class="flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800"
                    >
                      {{ membreLabel(membreId) }}
                      <button
                        type="button"
                        class="text-blue-500 hover:text-blue-800"
                        @click="removeSuggestedMember(role, membreId)"
                      >
                        ×
                      </button>
                    </span>
                  </div>

                  <!-- Select pour ajouter un membre -->
                  <div v-if="membresDisponibles.length > 0" class="form-select-wrapper">
                    <select
                      class="form-input form-input-sm form-select"
                      @change="
                        (e) => {
                          const val = (e.target as HTMLSelectElement).value
                          if (val) {
                            addSuggestedMember(role, val)
                            ;(e.target as HTMLSelectElement).value = ''
                          }
                        }
                      "
                    >
                      <option value="">— Ajouter un membre —</option>
                      <option
                        v-for="m in membresDisponibles.filter(
                          (x) => !role.membres_suggeres_ids.includes(x.id),
                        )"
                        :key="m.id"
                        :value="m.id"
                      >
                        {{ m.prenom }} {{ m.nom }}
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
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-3">
        <NuxtLink to="/planning/templates" class="btn btn-secondary">Annuler</NuxtLink>
        <button type="submit" :disabled="isSaving || !form.nom.trim()" class="btn btn-primary">
          {{ isSaving ? 'Sauvegarde…' : 'Sauvegarder' }}
        </button>
      </div>
    </form>
  </div>
</template>
