<template>
  <div class="space-y-4">
    <!-- Bloc 1 — En-tête : statut · type · date · lieu -->
    <div class="space-y-3 rounded-xl bg-slate-50 p-4">
      <div class="flex flex-wrap items-center gap-2">
        <span :class="currentStatusBadgeClass">{{ currentStatusLabel }}</span>
        <span class="text-[10px] text-slate-400">•</span>
        <span class="text-xs font-semibold text-slate-700">
          {{ event.extendedProps.typeActivite }}
        </span>
      </div>
      <div class="space-y-1.5">
        <div class="flex items-center gap-2 text-sm text-slate-600">
          <Calendar class="size-4 shrink-0 text-slate-400" />
          {{ formatDate(event.start as string) }}
        </div>
        <div class="flex items-center gap-2 text-sm text-slate-600">
          <Clock class="size-4 shrink-0 text-slate-400" />
          {{ formatTime(event.start as string) }} – {{ formatTime(event.end as string) }}
        </div>
        <div v-if="planning?.activite?.lieu" class="flex items-center gap-2 text-sm text-slate-600">
          <MapPin class="size-4 shrink-0 text-slate-400" />
          {{ planning.activite.lieu }}
        </div>
      </div>
    </div>

    <!-- Bloc 2 — Contexte organisationnel -->
    <div class="flex gap-3">
      <div class="flex-1 rounded-xl border border-slate-100 bg-white p-3">
        <p class="mb-1.5 text-[10px] font-bold tracking-wide text-slate-400 uppercase">Ministère</p>
        <div class="flex items-center gap-2">
          <div
            class="size-2 shrink-0 rounded-full"
            :style="{ backgroundColor: detailMinistreColor?.bg ?? event.backgroundColor }"
          ></div>
          <span class="text-xs font-medium text-slate-700">{{ detailMinistereNom }}</span>
        </div>
      </div>
      <div class="flex-1 rounded-xl border border-slate-100 bg-white p-3">
        <p class="mb-1.5 text-[10px] font-bold tracking-wide text-slate-400 uppercase">Campus</p>
        <span class="text-xs font-medium text-slate-700">{{ detailCampusNom }}</span>
      </div>
    </div>

    <!-- Bloc 3 — Créneaux & équipes -->
    <div v-if="planning?.slots?.length">
      <p class="mb-2 text-[10px] font-bold tracking-wide text-slate-400 uppercase">
        Créneaux ({{ planning.slots.length }})
      </p>
      <div class="space-y-3">
        <div
          v-for="slot in planning.slots"
          :key="slot.id"
          class="overflow-hidden rounded-xl border border-slate-200"
        >
          <!-- Header créneau -->
          <div
            class="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-2.5"
          >
            <div class="flex items-center gap-2">
              <Clock class="size-3.5 text-slate-400" />
              <span class="text-xs font-semibold text-slate-700">{{ slot.nom_creneau }}</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-[10px] text-slate-500">
                {{ formatTime(slot.date_debut) }} – {{ formatTime(slot.date_fin) }}
              </span>
              <span
                :class="
                  slot.filling_rate >= 100
                    ? 'rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-700'
                    : slot.affectations.length > 0
                      ? 'rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700'
                      : 'rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500'
                "
              >
                {{ slot.affectations.length }}/{{ slot.nb_personnes_requis }}
              </span>
            </div>
          </div>

          <!-- Barre de remplissage -->
          <div class="h-1 bg-slate-100">
            <div
              class="h-1 bg-emerald-500 transition-all"
              :style="{ width: Math.min(slot.filling_rate, 100) + '%' }"
            ></div>
          </div>

          <!-- Affectations -->
          <div class="divide-y divide-slate-50">
            <div
              v-for="aff in slot.affectations"
              :key="aff.id"
              class="flex items-center gap-3 px-4 py-2.5"
            >
              <div
                class="flex size-8 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white"
                :style="{
                  backgroundColor: ministreColorForAff(aff)?.bg ?? '#94A3B8',
                }"
              >
                {{ aff.membre?.prenom?.[0] }}{{ aff.membre?.nom?.[0] }}
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-xs font-semibold text-slate-800">
                  {{ aff.membre?.prenom }} {{ aff.membre?.nom }}
                </p>
                <p class="text-[10px] text-slate-400">
                  {{ roleLibelle(aff.role_code)
                  }}<template v-if="ministreNomForAff(aff)">
                    · {{ ministreNomForAff(aff) }}</template
                  >
                </p>
              </div>
              <span :class="affStatusBadge(aff.statut_affectation_code)">
                {{ affStatusLabel(aff.statut_affectation_code) }}
              </span>
            </div>
            <p v-if="!slot.affectations.length" class="px-4 py-3 text-xs text-slate-400 italic">
              Aucun membre assigné
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Bloc 4 — Répertoire de chants -->
    <div v-if="planning?.chants !== undefined" class="flex flex-col gap-2">
      <div class="flex items-center gap-2">
        <Music class="size-4 text-slate-400" />
        <span class="text-[11px] font-black tracking-widest text-slate-500 uppercase">
          Répertoire
        </span>
        <span
          v-if="planning.chants.length > 0"
          class="flex h-5 items-center justify-center rounded-full bg-slate-100 px-2 text-[10px] font-bold text-slate-500"
        >
          {{ planning.chants.length }}
        </span>
      </div>
      <PlanningRepertoire :chants="planning.chants" />
    </div>

    <!-- Bloc 5 — Résumé global -->
    <div
      v-if="planning?.slots?.length"
      class="flex items-center gap-4 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3"
    >
      <div class="flex items-center gap-1.5 text-xs text-slate-600">
        <UsersIcon class="size-3.5 text-slate-400" />
        <span class="font-semibold">{{ totalMembresUniques }}</span>
        membre{{ totalMembresUniques !== 1 ? 's' : '' }}
      </div>
      <div class="h-3 w-px bg-slate-200"></div>
      <div class="flex items-center gap-1.5 text-xs text-slate-600">
        <Clock class="size-3.5 text-slate-400" />
        <span class="font-semibold">{{ planning.slots.length }}</span>
        créneau{{ planning.slots.length !== 1 ? 'x' : '' }}
      </div>
      <div class="ml-auto flex items-center gap-2">
        <div class="h-1.5 w-16 rounded-full bg-slate-200">
          <div
            class="h-1.5 rounded-full bg-emerald-500 transition-all"
            :style="{ width: globalFillRate + '%' }"
          ></div>
        </div>
        <span class="text-[10px] font-semibold text-slate-500">{{ globalFillRate }}%</span>
      </div>
    </div>

    <!-- Confirmation annulation -->
    <div v-if="confirmingCancel" class="space-y-3 rounded-xl border border-red-200 bg-red-50 p-4">
      <p class="text-sm font-semibold text-red-700">Annuler ce planning ?</p>
      <p class="text-xs text-red-500">
        Cette action est irréversible. Le planning passera au statut ANNULÉ.
      </p>
      <div class="flex gap-2">
        <button
          class="btn btn-danger btn-sm flex-1"
          :disabled="isUpdating"
          @click="executeStatusChange('ANNULE')"
        >
          {{ isUpdating ? 'Annulation...' : "Confirmer l'annulation" }}
        </button>
        <button class="btn btn-ghost btn-sm" @click="confirmingCancel = false">Non</button>
      </div>
    </div>

    <!-- Confirmation suppression -->
    <div v-if="confirmingDelete" class="space-y-3 rounded-xl border border-red-200 bg-red-50 p-4">
      <p class="text-sm font-semibold text-red-700">Supprimer ce planning ?</p>
      <p class="text-xs text-red-500">
        Cette action est irréversible. Toutes les données seront perdues.
      </p>
      <div class="flex gap-2">
        <button
          class="btn btn-danger btn-sm flex-1"
          :disabled="isDeleting"
          @click="executeDelete()"
        >
          {{ isDeleting ? 'Suppression...' : 'Confirmer la suppression' }}
        </button>
        <button class="btn btn-ghost btn-sm" @click="confirmingDelete = false">Non</button>
      </div>
    </div>

    <!-- Erreur workflow -->
    <p v-if="workflowError" class="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
      {{ workflowError }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import { Calendar, Clock, MapPin, Music, Users as UsersIcon } from 'lucide-vue-next'
import { planningWorkflowKey } from '../composables/usePlanningWorkflow'
import { planningDetailHelpersKey } from '../composables/usePlanningDetailHelpers'
import PlanningRepertoire from './PlanningRepertoire.vue'
import type { PlanningEvent, PlanningFullRead } from '../types/planning.types'

defineProps<{
  event: PlanningEvent
  planning: PlanningFullRead | null | undefined
}>()

// Destructurer pour bénéficier de l'auto-unwrap des refs dans le template
const {
  confirmingCancel,
  confirmingDelete,
  workflowError,
  isUpdating,
  isDeleting,
  executeStatusChange,
  executeDelete,
  currentStatusBadgeClass,
  currentStatusLabel,
} = inject(planningWorkflowKey)!

const {
  detailMinistreColor,
  detailMinistereNom,
  detailCampusNom,
  totalMembresUniques,
  globalFillRate,
  formatDate,
  formatTime,
  ministreColorForAff,
  ministreNomForAff,
  roleLibelle,
  affStatusBadge,
  affStatusLabel,
} = inject(planningDetailHelpersKey)!
</script>
