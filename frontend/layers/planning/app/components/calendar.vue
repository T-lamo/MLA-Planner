<template>
  <div class="space-y-6">
    <div class="flex flex-col justify-between gap-4 md:flex-row md:items-center">
      <CalendarPerspectiveToggle v-model="activePerspective" />

      <div class="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-2">
        <span class="text-xs font-medium text-slate-400">Campus Actif</span>
        <div class="h-4 w-px bg-slate-200"></div>
        <span class="text-xs font-bold text-(--color-primary-700)">{{ ui.selectedCampus }}</span>
      </div>
    </div>

    <AppCalendar
      :events="filteredEvents"
      @event-click="handleEventClick"
      @date-select="handleDateSelect"
    />

    <PlanningDetailDrawer :event="selectedEvent" @close="selectedEvent = null" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { DateSelectArg, EventApi } from '@fullcalendar/core'
import { useUIStore } from '~~/layers/base/app/stores/useUiStore'
import type {
  PlanningEvent,
  PlanningViewPerspective,
  PlanningEventMetadata,
} from '../types/planning.types'

// État
const ui = useUIStore()
const selectedEvent = ref<PlanningEvent | null>(null)
const activePerspective = ref<PlanningViewPerspective>('CAMPUS')

// Mock Constants (Simulation Auth / Contexte)
const CURRENT_USER_ID = 'user-001'
const USER_MINISTERE_ID = 'M_LOUANGE'

// Données statiques
const rawEvents = ref<PlanningEvent[]>([
  {
    id: 'evt-1',
    title: 'Culte de Célébration',
    start: '2026-02-23T10:00:00',
    end: '2026-02-23T12:00:00',
    backgroundColor: '#6366f1',
    extendedProps: {
      campus: 'Paris - Cité Royale',
      ministereId: 'M_LOUANGE',
      ministereLabel: 'Louange',
      typeActivite: 'Culte',
      statut: 'VALIDÉ',
      membreIds: ['user-001', 'user-005'],
      responsableId: 'user-005',
    },
  },
  {
    id: 'evt-2',
    title: 'Répétition Technique',
    start: '2026-02-22T15:00:00',
    end: '2026-02-22T17:00:00',
    backgroundColor: '#f59e0b',
    extendedProps: {
      campus: 'Paris - Cité Royale',
      ministereId: 'M_TECH',
      ministereLabel: 'Technique',
      typeActivite: 'Formation',
      statut: 'BROUILLON',
      membreIds: ['user-009'],
      responsableId: 'user-001',
    },
  },
])

/**
 * Logique de filtrage réactive
 */
const filteredEvents = computed<PlanningEvent[]>(() => {
  return rawEvents.value
    .filter((event) => event.extendedProps.campus === ui.selectedCampus)
    .map((event) => ({
      ...event,
      extendedProps: {
        ...event.extendedProps,
        isPersonal:
          event.extendedProps.membreIds.includes(CURRENT_USER_ID) ||
          event.extendedProps.responsableId === CURRENT_USER_ID,
      },
    }))
    .filter((event) => {
      if (activePerspective.value === 'PERSONAL') return event.extendedProps.isPersonal
      if (activePerspective.value === 'MINISTERE')
        return event.extendedProps.ministereId === USER_MINISTERE_ID
      return true
    })
})

/**
 * handleEventClick reçoit maintenant directement l'EventApi
 */
const handleEventClick = (eventApi: EventApi): void => {
  // Plus besoin de chercher eventApi.event, car l'enfant l'a déjà extrait
  if (!eventApi) return

  selectedEvent.value = {
    id: eventApi.id,
    title: eventApi.title,
    start: eventApi.startStr || eventApi.start?.toISOString() || '',
    end: eventApi.endStr || eventApi.end?.toISOString() || '',
    backgroundColor: eventApi.backgroundColor,
    // Cast sécurisé vers notre interface de métadonnées
    extendedProps: eventApi.extendedProps as PlanningEventMetadata,
  }
}

/**
 * Gestion de la sélection d'une plage de dates
 * Typage strict via DateSelectArg
 */
const handleDateSelect = (_selectInfo: DateSelectArg): void => {
  // console.log('📅 Nouvelle réservation demandée du :', selectInfo.startStr, 'au', selectInfo.endStr)
  // Ici, on pourrait ouvrir un tiroir de création
}
</script>
