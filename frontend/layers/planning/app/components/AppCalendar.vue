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
import { computed, ref, onMounted, onUnmounted, h } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import listPlugin from '@fullcalendar/list'
import interactionPlugin from '@fullcalendar/interaction'
import allLocales from '@fullcalendar/core/locales-all'
import type {
  EventClickArg,
  DateSelectArg,
  CalendarOptions,
  EventApi,
  EventContentArg,
} from '@fullcalendar/core'
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

  eventClick: (info: EventClickArg) => emit('event-click', info.event),
  select: (info: DateSelectArg) => emit('date-select', info),

  eventClassNames: (arg: { event: EventApi }) => {
    const isPersonal = arg.event.extendedProps.isPersonal ? 'is-personal' : ''
    const status = String(arg.event.extendedProps.statut || 'brouillon').toLowerCase()
    return ['mla-calendar-event', `status-${status}`, isPersonal].filter(Boolean)
  },

  // Vue liste : dot coloré par ministère + titre
  eventContent: (arg: EventContentArg) => {
    if (arg.view.type.startsWith('list')) {
      return h('div', { class: 'fc-list-custom-event' }, [
        h('span', {
          class: 'list-event-dot',
          style: { backgroundColor: arg.event.backgroundColor },
        }),
        h('span', { class: 'list-event-title' }, arg.event.title),
      ])
    }
    return true
  },
}))
</script>
<style>
@reference "~~/layers/base/app/assets/css/main.css";

/* ── Variables FullCalendar ─────────────────────────────────────────── */
.fc {
  @apply p-2 font-sans text-slate-700 md:p-4;
  --fc-border-color: #f1f5f9;
  --fc-button-bg-color: #ffffff;
  --fc-button-border-color: #e2e8f0;
  --fc-button-text-color: #475569;
  --fc-button-hover-bg-color: #f8fafc;
  --fc-button-hover-border-color: #cbd5e1;
  --fc-button-active-bg-color: var(--color-primary-600);
  --fc-button-active-border-color: var(--color-primary-600);
  --fc-now-indicator-color: var(--color-primary-600);
}

/* ── Toolbar ────────────────────────────────────────────────────────── */
.fc .fc-toolbar {
  @apply mb-6 flex-col gap-3 md:flex-row;
}
.fc .fc-toolbar-title {
  @apply text-base font-bold capitalize text-slate-800 md:text-lg;
}

/* ── Boutons ────────────────────────────────────────────────────────── */
.fc .fc-button {
  @apply px-2 py-2 text-[10px] font-semibold shadow-none outline-none transition-all md:px-4 md:text-xs;
  border-radius: 8px;
}
.fc .fc-button-active,
.fc .fc-button:focus-visible {
  background-color: var(--color-primary-600) !important; /* active state — FullCalendar override */
  border-color: var(--color-primary-600) !important;
  color: #ffffff !important;
}
.fc .fc-button:hover:not(.fc-button-active) {
  background-color: #f8fafc !important;
  border-color: #cbd5e1 !important;
}

/* ── Responsive mobile ──────────────────────────────────────────────── */
@media (max-width: 767px) {
  .fc .fc-daygrid-day-number {
    @apply p-1 text-xs;
  }
  .fc .fc-timegrid-axis-cushion {
    @apply p-0 text-[10px];
  }
  .fc .fc-toolbar-chunk {
    @apply flex w-full justify-center;
  }
}

/* ── Événements — base ──────────────────────────────────────────────── */
/* NE PAS écraser background-color ni border-color ici :
   FullCalendar les pose en inline style depuis backgroundColor/borderColor de l'event */
.fc-timegrid-event {
  @apply rounded-lg shadow-sm;
  border-left-width: 4px; /* épaissit la bordure gauche déjà colorée inline */
}

.mla-calendar-event {
  @apply cursor-pointer rounded-md border-none px-1 py-0.5 text-[10px]
         font-medium shadow-sm transition-transform active:scale-95 md:px-2 md:text-xs;
}

/* ── Indicateur événement personnel ────────────────────────────────── */
.mla-calendar-event.is-personal {
  position: relative;
}
.mla-calendar-event.is-personal::before {
  content: '';
  position: absolute;
  top: 3px;
  right: 3px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.9);
  pointer-events: none;
  z-index: 2;
}

/* ── Statuts ────────────────────────────────────────────────────────── */
.status-brouillon {
  opacity: 0.85;
  position: relative;
}
.status-brouillon::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 4px,
    rgba(255, 255, 255, 0.22) 4px,
    rgba(255, 255, 255, 0.22) 8px
  );
  pointer-events: none;
}

/* ANNULE / TERMINE : override du bg inline de FullCalendar — voulu */
.status-annule {
  background-color: #94a3b8 !important; /* slate-400 — remplace couleur ministère */
  border-color: #94a3b8 !important;
  color: #ffffff !important;
}
.status-annule .fc-event-title {
  text-decoration: line-through;
  text-decoration-color: rgba(255, 255, 255, 0.7);
}

.status-termine {
  background-color: #e2e8f0 !important; /* slate-200 — remplace couleur ministère */
  border-color: #cbd5e1 !important;
  color: #64748b !important; /* slate-500 */
  opacity: 0.75;
}

/* ── Vue liste — custom eventContent ───────────────────────────────── */
.fc-list-event {
  @apply cursor-pointer;
}
.fc-list-event:hover td {
  @apply bg-slate-50;
}
.fc-list-custom-event {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 0;
}
.list-event-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.list-event-title {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #334155;
}

/* ── Indicateur "maintenant" ────────────────────────────────────────── */
.fc-timegrid-now-indicator-line {
  @apply border-primary-600;
}
</style>
