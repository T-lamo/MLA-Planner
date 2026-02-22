<template>
  <div
    class="calendar-wrapper relative min-h-[500px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm md:min-h-[650px]"
  >
    <ClientOnly>
      <FullCalendar ref="fullCalendarRef" :options="calendarOptions" />

      <template #fallback>
        <div class="space-y-4 p-4 md:p-8">
          <div class="flex items-center justify-between">
            <div class="h-8 w-32 animate-pulse rounded bg-slate-100 md:h-10 md:w-48"></div>
            <div class="h-8 w-24 animate-pulse rounded bg-slate-100 md:h-10 md:w-32"></div>
          </div>
          <div
            class="h-[400px] w-full animate-pulse rounded-xl border border-slate-100 bg-slate-50 md:h-[500px]"
          ></div>
        </div>
      </template>
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import listPlugin from '@fullcalendar/list'
import interactionPlugin from '@fullcalendar/interaction'
import allLocales from '@fullcalendar/core/locales-all'
// Imports des types officiels
import type { EventClickArg, DateSelectArg, CalendarOptions, EventApi } from '@fullcalendar/core'
import type { PlanningEvent } from '../types/planning.types'

const props = defineProps<{
  events: PlanningEvent[]
}>()

const emit = defineEmits<{
  /** * On émet l'objet EventApi de FullCalendar pour que le parent
   * puisse extraire les données proprement.
   */
  (e: 'event-click', event: EventApi): void
  (e: 'date-select', selectInfo: DateSelectArg): void
}>()

const fullCalendarRef = ref<InstanceType<typeof FullCalendar> | null>(null)
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// Typage explicite de la constante computed
const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin],
  initialView: isMobile.value ? 'listWeek' : 'dayGridMonth',
  locales: allLocales,
  locale: 'fr',
  firstDay: 1,

  headerToolbar: isMobile.value
    ? {
        left: 'prev,next',
        center: 'title',
        right: 'listWeek,timeGridDay',
      }
    : {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
      },

  buttonText: {
    today: isMobile.value ? 'Auj.' : "Aujourd'hui",
    month: 'Mois',
    week: 'Sem.',
    day: 'Jour',
    list: 'Liste',
  },

  allDaySlot: true,
  slotMinTime: '07:00:00',
  slotMaxTime: '22:00:00',
  slotLabelFormat: {
    hour: 'numeric',
    minute: '2-digit',
    omitZeroMinute: true,
    meridiem: 'short',
  },

  events: props.events,
  editable: true,
  selectable: true,
  selectMirror: true,
  dayMaxEvents: isMobile.value ? 2 : true,
  height: isMobile.value ? 'auto' : '700px',
  handleWindowResize: true,
  windowResizeDelay: 100,

  // Utilisation des types d'arguments de FullCalendar
  eventClick: (info: EventClickArg) => emit('event-click', info.event),
  select: (info: DateSelectArg) => emit('date-select', info),

  eventClassNames: (arg: { event: EventApi }) => {
    const isPersonal = arg.event.extendedProps.isPersonal ? 'is-personal' : ''
    // On convertit le statut en chaîne de caractères pour plus de sécurité
    const status = String(arg.event.extendedProps.statut || 'brouillon').toLowerCase()
    return ['mla-calendar-event', `status-${status}`, isPersonal]
  },
}))
</script>
<style>
@reference "~~/layers/base/app/assets/css/main.css";

/* Base FullCalendar */
.fc {
  @apply p-2 font-sans text-slate-700 md:p-4;
  --fc-border-color: #f1f5f9;
  --fc-button-bg-color: #ffffff;
  --fc-button-border-color: #e2e8f0;
  --fc-button-text-color: #475569;
  --fc-now-indicator-color: var(--color-primary-600);
}

/* Toolbar Responsive */
.fc .fc-toolbar {
  @apply mb-6 flex-col gap-3 md:flex-row;
}

.fc .fc-toolbar-title {
  @apply text-base font-bold text-slate-800 capitalize md:text-lg;
}

/* Boutons plus gros sur mobile pour le tactile */
.fc .fc-button {
  @apply px-2 py-2 text-[10px] font-semibold shadow-none transition-all outline-none md:px-4 md:text-xs;
}

/* Optimisation Mobile des Grilles */
@media (max-width: 767px) {
  .fc .fc-daygrid-day-number {
    @apply p-1 text-xs;
  }

  /* Cacher les colonnes de temps trop larges sur petit écran */
  .fc .fc-timegrid-axis-cushion {
    @apply p-0 text-[10px];
  }

  .fc .fc-toolbar-chunk {
    @apply flex w-full justify-center;
  }
}

/* Style des événements */
.fc-timegrid-event {
  @apply rounded-lg border-l-4 border-l-(--color-primary-600)! bg-(--color-primary-50)! shadow-sm;
}

.mla-calendar-event {
  @apply cursor-pointer rounded-md border-none px-1 py-0.5 text-[10px] font-medium shadow-sm transition-transform active:scale-95 md:px-2 md:text-xs;
}

.mla-calendar-event.is-personal {
  @apply ring-2 ring-(--color-primary-500) ring-offset-1;
}

.fc-v-event {
  @apply bg-(--color-primary-600);
}

.fc-timegrid-now-indicator-line {
  @apply border-(--color-primary-600);
}

/* Ajustement pour la vue liste sur mobile */
.fc-list-event {
  @apply cursor-pointer hover:bg-slate-50;
}
</style>
