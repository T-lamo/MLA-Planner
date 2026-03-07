<template>
  <div class="space-y-4">
    <!-- ================================================================
         HEADER : toggle perspective + sélecteur ministère + bouton création
         ================================================================ -->
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div class="flex flex-col gap-3">
        <!-- Toggle PERSONAL / MINISTERE / CAMPUS -->
        <CalendarPerspectiveToggle :modelValue="perspective" @update:model-value="setView" />

        <!-- Sélecteur de ministère (visible uniquement si MINISTERE et > 1 ministère) -->
        <div
          v-if="perspective === 'MINISTERE' && ministeres.length > 1"
          class="flex flex-wrap gap-2"
        >
          <button
            class="rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all"
            :class="
              activeMinistereId === null
                ? 'border-slate-300 bg-slate-800 text-white'
                : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
            "
            @click="setMinistere(null)"
          >
            Tous
          </button>
          <button
            v-for="m in ministeres"
            :key="m.id"
            class="rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all"
            :style="
              activeMinistereId === m.id
                ? {
                    backgroundColor: ministereColorMap.get(m.id)?.bg,
                    borderColor: ministereColorMap.get(m.id)?.border,
                    color: ministereColorMap.get(m.id)?.text,
                  }
                : {
                    borderColor: ministereColorMap.get(m.id)?.border,
                    color: ministereColorMap.get(m.id)?.bg,
                  }
            "
            @click="setMinistere(m.id)"
          >
            {{ m.nom }}
          </button>
        </div>
      </div>

      <!-- Bouton "Nouveau planning" (desktop uniquement) -->
      <button
        v-if="canCreatePlanning"
        class="bg-primary-600 hover:bg-primary-700 hidden items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold text-white shadow-sm transition-colors sm:flex"
        @click="openCreateModal(null)"
      >
        <Plus class="size-4" />
        Nouveau planning
      </button>
    </div>

    <!-- ================================================================
         LÉGENDE COULEURS — un chip par ministère
         ================================================================ -->
    <div v-if="ministeres.length > 0" class="flex flex-wrap items-center gap-3">
      <span class="text-[10px] font-bold tracking-wider text-slate-400 uppercase"> Légende </span>
      <div
        v-for="m in ministeres"
        :key="m.id"
        class="flex min-h-8 cursor-pointer items-center gap-2 rounded-full border
               px-3 py-1.5 text-xs font-medium transition-opacity"
        :style="{
          backgroundColor: ministereColorMap.get(m.id)?.light,
          borderColor: ministereColorMap.get(m.id)?.border,
          color: ministereColorMap.get(m.id)?.bg,
          opacity: legendFilter !== null && legendFilter !== m.id ? '0.35' : '1',
        }"
        @click="toggleLegendFilter(m.id)"
      >
        <div
          class="size-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: ministereColorMap.get(m.id)?.bg }"
        ></div>
        {{ m.nom }}
      </div>

      <!-- Bouton réinitialiser filtre légende -->
      <button
        v-if="legendFilter !== null"
        class="text-[10px] font-medium text-slate-400 underline hover:text-slate-600"
        @click="legendFilter = null"
      >
        Tout afficher
      </button>
    </div>

    <!-- ================================================================
         ÉTAT ERREUR
         ================================================================ -->
    <div
      v-if="error && !isLoading"
      class="flex flex-col items-center gap-4 rounded-xl border border-red-100 bg-red-50 px-6 py-10 text-center"
    >
      <AlertCircle class="size-10 text-red-400" />
      <div class="space-y-1">
        <p class="text-sm font-semibold text-red-700">Impossible de charger le planning</p>
        <p class="text-xs text-red-500">{{ error }}</p>
      </div>
      <button
        class="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-red-700"
        @click="refresh"
      >
        Réessayer
      </button>
    </div>

    <!-- ================================================================
         SKELETON LOADING
         ================================================================ -->
    <div
      v-else-if="isLoading"
      class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:p-6"
    >
      <div class="flex items-center justify-between">
        <div class="h-7 w-36 animate-pulse rounded-lg bg-slate-100 md:w-52"></div>
        <div class="flex gap-2">
          <div class="h-7 w-16 animate-pulse rounded-lg bg-slate-100"></div>
          <div class="h-7 w-16 animate-pulse rounded-lg bg-slate-100"></div>
          <div class="h-7 w-16 animate-pulse rounded-lg bg-slate-100"></div>
        </div>
      </div>
      <!-- Grille calendrier factice -->
      <div class="grid grid-cols-7 gap-1">
        <div v-for="i in 7" :key="`hd-${i}`" class="h-6 animate-pulse rounded bg-slate-100"></div>
        <div
          v-for="i in 35"
          :key="`cell-${i}`"
          class="h-20 animate-pulse rounded-lg border border-slate-50 bg-slate-50 md:h-28"
        ></div>
      </div>
    </div>

    <!-- ================================================================
         ÉTAT VIDE — aucun planning pour la perspective active
         ================================================================ -->
    <div
      v-else-if="filteredEvents.length === 0"
      class="flex flex-col items-center gap-5 rounded-xl border border-slate-200 bg-white py-16 text-center shadow-sm"
    >
      <div class="flex size-16 items-center justify-center rounded-2xl bg-slate-50">
        <CalendarDays class="size-8 text-slate-300" />
      </div>
      <div class="space-y-1.5">
        <p class="font-semibold text-slate-700">{{ emptyStateTitle }}</p>
        <p class="max-w-xs text-sm text-slate-400">{{ emptyStateMessage }}</p>
      </div>
      <button
        v-if="canCreatePlanning"
        class="bg-primary-600 hover:bg-primary-700 flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold text-white shadow-sm transition-colors"
        @click="openCreateModal(null)"
      >
        <Plus class="size-4" />
        Créer un premier planning
      </button>
    </div>

    <!-- ================================================================
         CALENDRIER FULLCALENDAR
         ================================================================ -->
    <AppCalendar
      v-else
      :events="filteredEvents"
      @event-click="onEventClick"
      @date-select="onDateSelect"
    />

    <!-- ================================================================
         DRAWER DE DÉTAIL
         ================================================================ -->
    <PlanningDetailDrawer :event="selectedEvent" @close="selectedEvent = null" />

    <!-- ================================================================
         FAB — mobile uniquement
         ================================================================ -->
    <button
      v-if="canCreatePlanning"
      class="bg-primary-600 hover:bg-primary-700 fixed right-6 bottom-6 z-50 flex size-14 items-center justify-center rounded-full text-white shadow-lg transition-transform active:scale-95 sm:hidden"
      @click="openCreateModal(null)"
    >
      <Plus class="size-6" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, CalendarDays, AlertCircle } from 'lucide-vue-next'
import type { EventApi, DateSelectArg } from '@fullcalendar/core'
import { usePlanning } from '../../composables/usePlanning'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import type { PlanningEvent, PlanningEventMetadata } from '../../types/planning.types'

// -----------------------------------------------------------------------
// Composable principal
// -----------------------------------------------------------------------
const {
  perspective,
  activeMinistereId,
  ministeres,
  ministereColorMap,
  events,
  isLoading,
  error,
  setView,
  setMinistere,
  refresh,
} = usePlanning()

const authStore = useAuthStore()

// -----------------------------------------------------------------------
// Droits de création
// -----------------------------------------------------------------------
const canCreatePlanning = computed<boolean>(() => {
  const roles = authStore.currentUser?.roles ?? []
  return authStore.hasAdminAccess || roles.some((r) => r.toLowerCase().includes('responsable'))
})

// -----------------------------------------------------------------------
// Filtre légende (clic sur un chip filtre par ministère côté client)
// -----------------------------------------------------------------------
const legendFilter = ref<string | null>(null)

function toggleLegendFilter(ministereId: string): void {
  legendFilter.value = legendFilter.value === ministereId ? null : ministereId
}

const filteredEvents = computed<PlanningEvent[]>(() => {
  if (!legendFilter.value) return events.value
  return events.value.filter((e) => e.extendedProps.ministereId === legendFilter.value)
})

// -----------------------------------------------------------------------
// Drawer de détail
// -----------------------------------------------------------------------
const selectedEvent = ref<PlanningEvent | null>(null)

function onEventClick(eventApi: EventApi): void {
  selectedEvent.value = {
    id: eventApi.id,
    title: eventApi.title,
    start: eventApi.startStr || eventApi.start?.toISOString() || '',
    end: eventApi.endStr || eventApi.end?.toISOString(),
    backgroundColor: eventApi.backgroundColor,
    borderColor: eventApi.borderColor,
    textColor: eventApi.textColor,
    extendedProps: eventApi.extendedProps as PlanningEventMetadata,
  }
}

// -----------------------------------------------------------------------
// Sélection de date → pré-remplissage création (MLA-PLAN-06)
// -----------------------------------------------------------------------
const pendingDateSelect = ref<DateSelectArg | null>(null)

function onDateSelect(selectInfo: DateSelectArg): void {
  pendingDateSelect.value = selectInfo
  openCreateModal(selectInfo)
}

// -----------------------------------------------------------------------
// Modal de création (MLA-PLAN-06 — stub pour l'instant)
// -----------------------------------------------------------------------
function openCreateModal(_selectInfo: DateSelectArg | null): void {
  // TODO MLA-PLAN-06 : ouvrir PlanningFormModal avec date pré-remplie
}

// -----------------------------------------------------------------------
// Messages état vide selon la perspective
// -----------------------------------------------------------------------
const emptyStateTitle = computed<string>(() => {
  if (perspective.value === 'PERSONAL') return 'Aucun créneau programmé pour vous'
  if (perspective.value === 'MINISTERE') return 'Aucun planning pour ce ministère'
  return 'Aucun planning disponible sur ce campus'
})

const emptyStateMessage = computed<string>(() => {
  if (perspective.value === 'PERSONAL')
    return "Vous n'êtes affecté à aucun créneau dans les prochains jours."
  if (perspective.value === 'MINISTERE')
    return "Aucune activité n'a encore été planifiée pour ce ministère."
  return "Aucune activité n'est enregistrée pour ce campus pour le moment."
})

// -----------------------------------------------------------------------
// Chargement initial
// -----------------------------------------------------------------------
onMounted(() => {
  refresh()
})
</script>
