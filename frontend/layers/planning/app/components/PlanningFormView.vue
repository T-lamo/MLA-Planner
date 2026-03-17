<template>
  <form id="planningForm" class="flex flex-col gap-2 pb-10" @submit.prevent>
    <!-- Mini-preview sticky -->
    <div
      v-if="activiteForm.type || activiteForm.date_debut"
      class="sticky top-0 z-10 -mx-1 mb-2 rounded-xl border px-3 py-2"
      :style="{
        backgroundColor: selectedMinistereColor?.light ?? '#F8FAFC',
        borderColor: selectedMinistereColor?.border ?? '#E2E8F0',
      }"
    >
      <div class="flex items-center gap-2">
        <div
          class="size-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: selectedMinistereColor?.bg ?? '#94A3B8' }"
        ></div>
        <span class="text-xs font-semibold text-slate-700">
          {{ activiteForm.type || 'Activité' }}
        </span>
        <span v-if="activiteForm.date_debut" class="text-xs text-slate-400">
          — {{ formatPreviewDate(activiteForm.date_debut) }}
        </span>
        <span v-if="slotsForm.length > 0" class="ml-auto text-[10px] font-medium text-slate-400">
          {{ slotsForm.length }} créneau{{ slotsForm.length > 1 ? 'x' : '' }}
        </span>
      </div>
    </div>

    <!-- SECTION 1 — ACTIVITÉ -->
    <FormSection
      title="Activité"
      :icon="Calendar"
      :isOpen="activeSections.has('activite')"
      :badge="isSection1Complete ? '✓' : undefined"
      @toggle="toggleSection('activite')"
    >
      <!-- Type d'activité -->
      <div class="mb-4">
        <label class="mb-2 block text-xs font-semibold tracking-wide text-slate-500 uppercase">
          Type d'activité *
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="t in ACTIVITE_TYPES"
            :key="t"
            type="button"
            class="rounded-full border px-3 py-1 text-xs font-medium transition-all"
            :class="
              activiteForm.type === t
                ? 'border-transparent text-white'
                : 'border-slate-200 text-slate-500 hover:border-slate-300 hover:text-slate-700'
            "
            :style="
              activiteForm.type === t
                ? { backgroundColor: selectedMinistereColor?.bg ?? '#3B82F6' }
                : {}
            "
            @click="activiteForm.type = t"
          >
            {{ t }}
          </button>
        </div>
      </div>

      <!-- Dates -->
      <div class="mb-4 grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
            >Début *</label
          >
          <input
            v-model="activiteForm.date_debut"
            type="datetime-local"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
            @change="onDateDebutChange"
          />
        </div>
        <div>
          <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
            >Fin *</label
          >
          <input
            v-model="activiteForm.date_fin"
            type="datetime-local"
            class="w-full rounded-lg border px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
            :class="dateError ? 'border-red-300 bg-red-50' : 'border-slate-200'"
            :min="activiteForm.date_debut"
          />
          <p v-if="dateError" class="mt-1 text-xs text-red-500">{{ dateError }}</p>
        </div>
      </div>

      <!-- Lieu -->
      <div class="mb-4">
        <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
          >Lieu</label
        >
        <input
          v-model="activiteForm.lieu"
          type="text"
          placeholder="Ex : Salle principale, Auditorium..."
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-300 focus:border-blue-400 focus:outline-none"
        />
      </div>

      <!-- Campus -->
      <div class="mb-4">
        <label class="mb-2 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
          >Campus *</label
        >
        <div v-if="userCampuses.length > 0" class="flex flex-wrap gap-2">
          <button
            v-for="c in userCampuses"
            :key="c.id"
            type="button"
            class="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all"
            :class="
              activiteForm.campus_id === c.id
                ? 'border-primary-300 bg-primary-50 text-primary-700'
                : userCampuses.length === 1
                  ? 'cursor-default border-slate-200 bg-slate-50 text-slate-600'
                  : 'border-slate-200 bg-slate-50 text-slate-500 hover:border-slate-300 hover:text-slate-700'
            "
            :disabled="userCampuses.length === 1"
            @click="((activiteForm.campus_id = c.id), loadMinistreresForCampus(c.id))"
          >
            <MapPin class="size-3 shrink-0" />
            {{ c.nom }}
          </button>
        </div>
        <p v-else class="text-xs text-slate-400 italic">Aucun campus assigné à votre profil.</p>
      </div>

      <!-- Ministère -->
      <div class="mb-4">
        <label class="mb-2 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
          >Ministère *</label
        >
        <p v-if="!activiteForm.campus_id" class="text-xs text-slate-400 italic">
          Sélectionnez d'abord un campus.
        </p>
        <p v-else-if="isLoadingMinisteres" class="text-xs text-slate-400">Chargement...</p>
        <p v-else-if="campusMinisteres.length === 0" class="text-xs text-slate-400 italic">
          Aucun ministère pour ce campus.
        </p>
        <div v-else class="flex flex-wrap gap-2">
          <button
            v-for="m in campusMinisteres"
            :key="m.id"
            type="button"
            class="flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all"
            :style="
              activiteForm.ministere_organisateur_id === m.id
                ? {
                    backgroundColor: campusMinistereColorMap.get(m.id)?.bg,
                    borderColor: campusMinistereColorMap.get(m.id)?.bg,
                    color: campusMinistereColorMap.get(m.id)?.text,
                  }
                : {
                    borderColor: campusMinistereColorMap.get(m.id)?.border,
                    color: campusMinistereColorMap.get(m.id)?.bg,
                    backgroundColor: campusMinistereColorMap.get(m.id)?.light,
                  }
            "
            @click="selectMinistere(m.id)"
          >
            <span
              class="size-2 rounded-full"
              :style="{ backgroundColor: campusMinistereColorMap.get(m.id)?.bg }"
            ></span>
            {{ m.nom }}
          </button>
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase">
          Description
          <span class="font-normal text-slate-400 normal-case">(optionnel)</span>
        </label>
        <textarea
          v-model="activiteForm.description"
          rows="2"
          placeholder="Notes, instructions particulières..."
          class="w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-300 focus:border-blue-400 focus:outline-none"
        ></textarea>
      </div>
    </FormSection>

    <!-- SECTION 2 — CRÉNEAUX -->
    <div :class="{ 'pointer-events-none opacity-40': !isSection1Complete }">
      <FormSection
        title="Créneaux"
        :icon="Clock"
        :isOpen="activeSections.has('creneaux')"
        :badge="slotsForm.length > 0 ? slotsForm.length : undefined"
        @toggle="toggleSection('creneaux')"
      >
        <div class="mb-3 flex justify-end">
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-lg border border-dashed border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:border-slate-400 hover:text-slate-700"
            @click="addSlot"
          >
            <Plus class="size-3.5" />
            Ajouter un créneau
          </button>
        </div>

        <div class="space-y-3">
          <div
            v-for="(slot, si) in slotsForm"
            :key="slot._tempId"
            class="rounded-xl border border-slate-200 bg-slate-50 p-4"
          >
            <div class="mb-3 flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 uppercase">Créneau {{ si + 1 }}</span>
              <button
                v-if="slotsForm.length > 1"
                type="button"
                class="rounded-full p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                @click="removeSlot(si)"
              >
                <Trash2 class="size-3.5" />
              </button>
            </div>

            <div class="mb-3">
              <label class="mb-1 block text-xs font-medium text-slate-500">Libellé</label>
              <input
                v-model="slot.nom_creneau"
                type="text"
                placeholder="Ex : Équipe Louange, Accueil..."
                class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-300 focus:border-blue-400 focus:outline-none"
              />
            </div>

            <div class="mb-3 grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-500">Heure début</label>
                <input
                  v-model="slot.heure_debut"
                  type="time"
                  step="60"
                  class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
                />
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-500">Heure fin</label>
                <input
                  v-model="slot.heure_fin"
                  type="time"
                  step="60"
                  class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label class="mb-1 block text-xs font-medium text-slate-500"
                >Personnes requises</label
              >
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="flex size-7 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-100 disabled:opacity-40"
                  :disabled="slot.nb_personnes_requis <= 1"
                  @click="slot.nb_personnes_requis--"
                >
                  <Minus class="size-3" />
                </button>
                <span class="w-6 text-center text-sm font-bold text-slate-700">{{
                  slot.nb_personnes_requis
                }}</span>
                <button
                  type="button"
                  class="flex size-7 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-100"
                  @click="slot.nb_personnes_requis++"
                >
                  <Plus class="size-3" />
                </button>
              </div>
            </div>
          </div>

          <p v-if="slotsForm.length === 0" class="text-sm text-slate-400 italic">
            Ajoutez au moins un créneau pour configurer les affectations.
          </p>
        </div>
      </FormSection>
    </div>

    <!-- SECTION 3 — ÉQUIPE -->
    <div
      :class="{ 'pointer-events-none opacity-40': !isSection1Complete || slotsForm.length === 0 }"
    >
      <FormSection
        title="Équipe assignée"
        :icon="UsersIcon"
        :isOpen="activeSections.has('equipe')"
        :badge="totalAffectations > 0 ? totalAffectations : undefined"
        @toggle="toggleSection('equipe')"
      >
        <div class="space-y-4">
          <div
            v-for="(slot, si) in slotsForm"
            :key="slot._tempId"
            class="rounded-xl border border-slate-200 bg-white"
          >
            <div class="flex items-center justify-between border-b border-slate-100 px-4 py-2.5">
              <span class="text-xs font-bold text-slate-700">
                {{ slot.nom_creneau || `Créneau ${si + 1}` }}
              </span>
              <span
                class="rounded-full px-2 py-0.5 text-[10px] font-bold"
                :class="
                  slot.affectations.length >= slot.nb_personnes_requis
                    ? 'bg-emerald-100 text-emerald-600'
                    : slot.affectations.length > 0
                      ? 'bg-amber-100 text-amber-600'
                      : 'bg-slate-100 text-slate-400'
                "
              >
                {{ slot.affectations.length }}/{{ slot.nb_personnes_requis }}
              </span>
            </div>

            <div class="p-3">
              <div class="mb-2 space-y-2">
                <div
                  v-for="(aff, ai) in slot.affectations"
                  :key="aff._tempId"
                  class="flex items-center gap-2"
                >
                  <div
                    class="flex size-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
                    :style="{ backgroundColor: selectedMinistereColor?.bg ?? '#94A3B8' }"
                  >
                    {{ aff.membre_prenom[0] }}{{ aff.membre_nom[0] }}
                  </div>
                  <span class="flex-1 text-xs font-medium text-slate-700">
                    {{ aff.membre_prenom }} {{ aff.membre_nom }}
                  </span>
                  <select
                    v-model="aff.role_code"
                    class="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600 focus:border-blue-400 focus:outline-none"
                  >
                    <option value="" disabled>Rôle...</option>
                    <option
                      v-for="role in rolesForMembre(aff.membre_id)"
                      :key="role.code"
                      :value="role.code"
                    >
                      {{ role.libelle }}
                    </option>
                  </select>
                  <!-- Statut (lecture seule sauf planning PUBLIE) -->
                  <span
                    v-if="aff.statut_affectation_code && formTargetStatus !== 'PUBLIE'"
                    class="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                    :class="{
                      'bg-amber-100 text-amber-700': aff.statut_affectation_code === 'PROPOSE',
                      'bg-emerald-100 text-emerald-700': aff.statut_affectation_code === 'CONFIRME',
                      'bg-rose-100 text-rose-700': aff.statut_affectation_code === 'REFUSE',
                      'bg-blue-100 text-blue-700': aff.statut_affectation_code === 'PRESENT',
                      'bg-slate-100 text-slate-500': aff.statut_affectation_code === 'ABSENT',
                      'bg-orange-100 text-orange-700': aff.statut_affectation_code === 'RETARD',
                    }"
                    >{{ aff.statut_affectation_code }}</span
                  >
                  <select
                    v-if="aff.id && formTargetStatus === 'PUBLIE'"
                    v-model="aff.statut_affectation_code"
                    class="shrink-0 rounded-md border border-slate-200 bg-white px-1.5 py-1 text-[10px] text-slate-600 focus:border-blue-400 focus:outline-none"
                    @change="handleStatusChange(aff.id!, aff.statut_affectation_code!)"
                  >
                    <option value="PROPOSE">En attente</option>
                    <option value="CONFIRME">Confirmé</option>
                    <option value="REFUSE">Refusé</option>
                    <option value="PRESENT">Présent</option>
                    <option value="ABSENT">Absent</option>
                    <option value="RETARD">En retard</option>
                  </select>
                  <button
                    type="button"
                    class="shrink-0 rounded-full p-1 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-400"
                    @click="removeAffectation(si, ai)"
                  >
                    <X class="size-3" />
                  </button>
                </div>
              </div>

              <!-- Picker multi-ministère -->
              <div v-if="slotPickers[si]">
                <!-- Step 0 : bouton d'ouverture -->
                <button
                  v-if="!slotPickers[si].open"
                  type="button"
                  class="w-full rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-400 transition-colors hover:border-blue-300 hover:text-blue-500"
                  @click="slotPickers[si].open = true"
                >
                  + Ajouter un membre...
                </button>

                <!-- Picker ouvert -->
                <div v-else class="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-2">
                  <!-- Step 1 : choix du ministère -->
                  <div v-if="!slotPickers[si].ministereId">
                    <p
                      class="mb-1 text-[10px] font-semibold tracking-wide text-slate-400 uppercase"
                    >
                      Ministère
                    </p>
                    <div class="flex flex-wrap gap-1">
                      <button
                        v-for="min in campusMinisteres"
                        :key="min.id"
                        type="button"
                        class="rounded-full border px-2 py-0.5 text-xs font-medium transition-colors"
                        :style="{
                          borderColor: campusMinistereColorMap.get(min.id)?.bg ?? '#94A3B8',
                          color: campusMinistereColorMap.get(min.id)?.bg ?? '#94A3B8',
                        }"
                        @click="slotPickers[si].ministereId = min.id"
                      >
                        {{ min.nom }}
                      </button>
                    </div>
                  </div>

                  <!-- Step 2 : choix du membre -->
                  <template v-else-if="!slotPickers[si].memberId">
                    <div class="mb-1 flex items-center gap-1">
                      <button
                        type="button"
                        class="text-[10px] text-slate-400 hover:text-slate-600"
                        @click="slotPickers[si].ministereId = ''"
                      >
                        ← Retour
                      </button>
                      <span
                        class="ml-1 text-[10px] font-semibold tracking-wide text-slate-400 uppercase"
                      >
                        Membre
                      </span>
                    </div>
                    <input
                      v-model="slotPickers[si].memberQuery"
                      type="text"
                      placeholder="Rechercher..."
                      class="w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs focus:border-blue-300 focus:outline-none"
                    />
                    <div class="mt-1 max-h-36 space-y-0.5 overflow-y-auto">
                      <button
                        v-for="membre in pickerMembers(si)"
                        :key="membre.id"
                        type="button"
                        class="flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-xs hover:bg-white"
                        @click="selectPickerMember(si, membre)"
                      >
                        <div
                          class="flex size-6 shrink-0 items-center justify-center rounded-full text-[9px] font-bold text-white"
                          :style="{
                            backgroundColor:
                              campusMinistereColorMap.get(slotPickers[si].ministereId)?.bg ??
                              '#94A3B8',
                          }"
                        >
                          {{ membre.prenom[0] }}{{ membre.nom[0] }}
                        </div>
                        <span class="font-medium text-slate-700">
                          {{ membre.prenom }} {{ membre.nom }}
                        </span>
                        <!-- Badge indisponibilité (soft warning) -->
                        <span
                          v-if="isMemberUnavailable(membre.id)"
                          class="ml-auto shrink-0 rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] font-semibold text-amber-700"
                          :title="getWarningTooltip(membre.id)"
                        >
                          ⚠ Indisponible
                        </span>
                      </button>
                      <p
                        v-if="pickerMembers(si).length === 0"
                        class="px-2 py-1 text-xs text-slate-400 italic"
                      >
                        Aucun membre disponible
                      </p>
                    </div>
                  </template>

                  <!-- Step 3 : choix du rôle -->
                  <template v-else>
                    <div class="mb-1 flex items-center gap-1">
                      <button
                        type="button"
                        class="text-[10px] text-slate-400 hover:text-slate-600"
                        @click="slotPickers[si].memberId = ''"
                      >
                        ← Retour
                      </button>
                      <span
                        class="ml-1 text-[10px] font-semibold tracking-wide text-slate-400 uppercase"
                      >
                        Rôle — {{ slotPickers[si].memberPrenom }} {{ slotPickers[si].memberNom }}
                      </span>
                    </div>
                    <select
                      v-model="slotPickers[si].roleCode"
                      class="w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs focus:border-blue-300 focus:outline-none"
                    >
                      <option value="" disabled>Choisir un rôle...</option>
                      <option
                        v-for="role in pickerMemberRoles(si)"
                        :key="role.code"
                        :value="role.code"
                      >
                        {{ role.libelle }}
                      </option>
                    </select>
                    <div class="mt-1 flex gap-2">
                      <button
                        type="button"
                        :disabled="!slotPickers[si].roleCode"
                        class="flex-1 rounded-md bg-blue-500 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-blue-600 disabled:opacity-40"
                        @click="confirmAffectation(si)"
                      >
                        Confirmer
                      </button>
                      <button
                        type="button"
                        class="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-100"
                        @click="resetPicker(si)"
                      >
                        Annuler
                      </button>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <p v-if="slotsForm.length === 0" class="text-sm text-slate-400 italic">
            Définissez des créneaux avant d'assigner des membres.
          </p>
        </div>
      </FormSection>
    </div>
  </form>
</template>

<script setup lang="ts">
import { inject, watch } from 'vue'
import {
  X,
  Plus,
  Minus,
  Trash2,
  MapPin,
  Calendar,
  Clock,
  Users as UsersIcon,
} from 'lucide-vue-next'
import FormSection from '~~/layers/base/app/components/FormSection.vue'
import { planningFormKey } from '../composables/usePlanningForm'
import { ACTIVITE_TYPES } from '../types/planning.types'
import type { AffectationStatus } from '../types/planning.types'
import { useIndisponibiliteWarning } from '../composables/useIndisponibiliteWarning'
import { AffectationRepository } from '../repositories/AffectationRepository'

const affRepo = new AffectationRepository()
const notify = useMLANotify()

async function handleStatusChange(affId: string, newStatus: AffectationStatus) {
  try {
    await affRepo.updateStatus(affId, newStatus)
    notify.success('Statut mis à jour')
  } catch {
    // handled by global fetch interceptor
  }
}

// Destructurer pour bénéficier de l'auto-unwrap des refs dans le template
const {
  activeSections,
  activiteForm,
  slotsForm,
  slotPickers,
  isSection1Complete,
  totalAffectations,
  dateError,
  campusMinisteres,
  campusMinistereColorMap,
  isLoadingMinisteres,
  selectedMinistereColor,
  formTargetStatus,
  toggleSection,
  selectMinistere,
  onDateDebutChange,
  addSlot,
  removeSlot,
  removeAffectation,
  formatPreviewDate,
  pickerMembers,
  pickerMemberRoles,
  selectPickerMember,
  confirmAffectation,
  resetPicker,
  rolesForMembre,
  loadMinistreresForCampus,
} = inject(planningFormKey)!

// userCampuses est dans le shell (props) — le form a besoin de la liste pour le template.
// On re-expose via le form composable qui expose campusMinisteres pour les ministères,
// mais userCampuses vient du shell via un prop ou inject supplémentaire.
// Pour l'instant on l'injecte depuis le shell (voir PlanningDetailDrawer.vue).
const userCampuses = inject<Array<{ id: string; nom: string }>>('userCampuses')!

// --- Indisponibilités (soft warning) ---
const { isMemberUnavailable, getWarningTooltip, loadForPeriod } = useIndisponibiliteWarning()

watch(
  () => [activiteForm.campus_id, activiteForm.date_debut, activiteForm.date_fin],
  ([campusId, dateDebut, dateFin]) => {
    if (campusId && dateDebut && dateFin) {
      loadForPeriod(
        campusId as string,
        (dateDebut as string).slice(0, 10),
        (dateFin as string).slice(0, 10),
      )
    }
  },
  { immediate: true },
)
</script>
