<template>
  <div
    ref="calendarWrapperRef"
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
import { computed, ref, watch, onMounted, onUnmounted, h } from 'vue'
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
  EventDropArg,
} from '@fullcalendar/core'
import type { PlanningEvent, PlanningViewPerspective } from '../types/planning.types'

const props = defineProps<{
  events: PlanningEvent[]
  perspective?: PlanningViewPerspective
  userMinistereIds?: Set<string>
}>()

const emit = defineEmits<{
  /** On émet l'objet EventApi de FullCalendar pour que le parent
   * puisse extraire les données proprement.
   */
  (e: 'event-click', event: EventApi): void
  (e: 'date-select', selectInfo: DateSelectArg): void
  (
    e: 'event-drop',
    payload: { id: string; start: string; end: string | null; revert: () => void },
  ): void
}>()

const fullCalendarRef = ref<InstanceType<typeof FullCalendar> | null>(null)
const calendarWrapperRef = ref<HTMLDivElement | null>(null)
const isMobile = ref(false)
const calendarHeight = ref<number | string>('700px')

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const updateCalendarHeight = () => {
  if (isMobile.value) {
    calendarHeight.value = 'auto'
    return
  }
  const el = calendarWrapperRef.value
  if (!el) return
  const top = el.getBoundingClientRect().top
  calendarHeight.value = Math.max(400, window.innerHeight - top - 24)
}

const onResize = () => {
  checkMobile()
  updateCalendarHeight()
}

onMounted(() => {
  checkMobile()
  updateCalendarHeight()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})

// Sync impératif des dates quand un événement existant est mis à jour (ex : patchLocalPlanning).
// La liaison déclarative `events: props.events` ne met pas à jour la durée pour les IDs existants.
watch(
  () => props.events,
  (newEvents) => {
    const api = fullCalendarRef.value?.getApi()
    if (!api) return
    for (const evt of newEvents) {
      const fcEvent = api.getEventById(evt.id)
      if (fcEvent) {
        fcEvent.setDates(evt.start, evt.end ?? null)
      }
    }
  },
)

// Typage explicite de la constante computed
const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin],
  initialView: 'timeGridWeek',
  locales: allLocales,
  locale: 'fr',
  firstDay: 1,

  headerToolbar: isMobile.value
    ? {
        left: 'prev,next',
        center: 'title',
        right: 'timeGridWeek,timeGridDay,listWeek',
      }
    : {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
      },

  buttonIcons: false,
  buttonText: {
    prev: '‹',
    next: '›',
    today: isMobile.value ? 'Auj.' : "Aujourd'hui",
    week: 'Sem.',
    day: 'Jour',
    list: 'Liste',
    month: 'Mois',
  },

  allDaySlot: true,
  slotMinTime: '00:00:00',
  slotMaxTime: '24:00:00',
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
  height: isMobile.value ? 'auto' : calendarHeight.value,
  contentHeight: isMobile.value ? 'auto' : undefined,
  handleWindowResize: true,
  windowResizeDelay: 100,

  eventClick: (info: EventClickArg) => emit('event-click', info.event),
  select: (info: DateSelectArg) => emit('date-select', info),
  eventDrop: (info: EventDropArg) =>
    emit('event-drop', {
      id: info.event.id,
      start: info.event.startStr,
      end: info.event.endStr || null,
      revert: info.revert,
    }),

  eventClassNames: (arg: { event: EventApi }) => {
    const mId = String(arg.event.extendedProps.ministereId ?? '')
    const isDimmed =
      props.perspective === 'CAMPUS' &&
      !!props.userMinistereIds &&
      props.userMinistereIds.size > 0 &&
      !props.userMinistereIds.has(mId)
    const isPersonal = arg.event.extendedProps.isPersonal ? 'is-personal' : ''
    const status = String(arg.event.extendedProps.statut || 'brouillon').toLowerCase()
    return [
      'mla-calendar-event',
      `status-${status}`,
      isPersonal,
      isDimmed ? 'is-dimmed' : '',
    ].filter(Boolean)
  },

  // Vue liste : rendu enrichi (dot + titre + badge statut + méta campus/ministère)
  eventContent: (arg: EventContentArg) => {
    if (arg.view.type.startsWith('list')) {
      const statut = String(arg.event.extendedProps.statut || 'brouillon').toLowerCase()
      const ministereLabel =
        typeof arg.event.extendedProps.ministereLabel === 'string'
          ? arg.event.extendedProps.ministereLabel
          : ''
      const campus =
        typeof arg.event.extendedProps.campus === 'string' ? arg.event.extendedProps.campus : ''

      const statusLabels: Record<string, string> = {
        brouillon: 'Brouillon',
        publie: 'Publié',
        annule: 'Annulé',
        termine: 'Terminé',
      }
      const statusLabel = statusLabels[statut] ?? statut.toUpperCase()

      const metaChildren = [
        campus ? h('span', { class: 'mla-list-meta-chip' }, campus) : null,
        campus && ministereLabel ? h('span', { class: 'mla-list-meta-sep' }, '·') : null,
        ministereLabel ? h('span', { class: 'mla-list-meta-chip' }, ministereLabel) : null,
      ].filter(Boolean)

      return h('div', { class: 'mla-list-event' }, [
        h('span', {
          class: 'mla-list-dot',
          style: { backgroundColor: arg.event.backgroundColor },
        }),
        h('div', { class: 'mla-list-body' }, [
          h('div', { class: 'mla-list-top' }, [
            h('span', { class: 'mla-list-title' }, arg.event.title),
            h('span', { class: `mla-list-status mla-list-status--${statut}` }, statusLabel),
          ]),
          metaChildren.length > 0 ? h('div', { class: 'mla-list-meta' }, metaChildren) : null,
        ]),
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

/* ── Force la police système sur tous les éléments FC ───────────────── */
/* FullCalendar injecte Arial/Helvetica — on hérite du body             */
.fc,
.fc * {
  font-family: inherit;
}

/* ── Toolbar ────────────────────────────────────────────────────────── */
.fc .fc-toolbar {
  @apply mb-6 flex-col gap-3 md:flex-row;
}
.fc .fc-toolbar-title {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a; /* slate-900 */
  letter-spacing: -0.01em;
  text-transform: capitalize;
}
@media (min-width: 768px) {
  .fc .fc-toolbar-title {
    font-size: 1.125rem;
  }
}

/* ── Boutons ────────────────────────────────────────────────────────── */
.fc .fc-button {
  @apply px-2 py-2 text-[10px] font-semibold shadow-none transition-all outline-none md:px-4 md:text-xs;
  border-radius: 8px;
  letter-spacing: 0.01em;
}

/* ── Flèches prev / next (caractères Unicode — police native) ────────── */
.fc .fc-prev-button,
.fc .fc-next-button {
  font-size: 1.1rem;
  line-height: 1;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
}

/* ── En-têtes de colonnes (noms des jours) ──────────────────────────── */
.fc .fc-col-header-cell-cushion {
  font-size: 0.75rem; /* 12px */
  font-weight: 600;
  color: #475569; /* slate-600 */
  text-transform: capitalize;
  text-decoration: none;
  letter-spacing: 0.01em;
}

/* ── Numéros de jours (vue daygrid) ─────────────────────────────────── */
.fc .fc-daygrid-day-number {
  font-size: 0.8125rem; /* 13px */
  font-weight: 500;
  color: #64748b; /* slate-500 */
  text-decoration: none;
}
.fc .fc-day-today .fc-daygrid-day-number {
  font-weight: 700;
  color: var(--color-primary-600);
}

/* ── Labels des créneaux horaires ───────────────────────────────────── */
.fc .fc-timegrid-slot-label-cushion,
.fc .fc-timegrid-axis-cushion {
  font-size: 0.6875rem; /* 11px */
  font-weight: 500;
  color: #94a3b8; /* slate-400 */
  letter-spacing: 0.01em;
}

/* ── Entête "all-day" ───────────────────────────────────────────────── */
.fc .fc-timegrid-axis-cushion {
  font-size: 0.625rem; /* 10px */
  font-weight: 600;
  color: #cbd5e1; /* slate-300 */
  text-transform: uppercase;
  letter-spacing: 0.06em;
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
    padding: 2px 4px;
    font-size: 0.75rem;
  }
  .fc .fc-timegrid-axis-cushion {
    padding: 0;
    font-size: 0.5625rem; /* 9px */
  }
  .fc .fc-toolbar-chunk {
    @apply flex w-full justify-center;
  }
  .fc .fc-timegrid-col-frame {
    min-width: 40px;
  }
  .fc .fc-col-header-cell-cushion {
    padding: 4px 2px;
    font-size: 0.625rem; /* 10px */
  }
  .fc .fc-timegrid-slot-label-cushion {
    padding: 0 2px;
    font-size: 0.5625rem; /* 9px */
  }
  .fc-timegrid-event .fc-event-title {
    font-size: 0.625rem; /* 10px */
    display: -webkit-box;
    -webkit-line-clamp: 1;
    line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
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
  @apply cursor-pointer rounded-md border-none px-1 py-0.5 shadow-sm transition-transform active:scale-95 md:px-2;
  font-size: 0.6875rem; /* 11px — plus lisible que 10px */
  font-weight: 600;
  letter-spacing: 0.005em;
  line-height: 1.35;
}
@media (min-width: 768px) {
  .mla-calendar-event {
    font-size: 0.75rem; /* 12px desktop */
  }
}

/* Titre dans les événements timegrid */
.fc-timegrid-event .fc-event-title {
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.3;
  letter-spacing: 0.005em;
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

/* ── Vue CAMPUS — ministères non rattachés à l'utilisateur ─────────── */
/* Chaque ministère conserve sa couleur propre, simplement atténuée     */
.mla-calendar-event.is-dimmed {
  opacity: 0.38;
  filter: saturate(0.4);
  transition:
    opacity 0.2s ease,
    filter 0.2s ease;
}
.mla-calendar-event.is-dimmed:hover {
  opacity: 0.7;
  filter: saturate(0.75);
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

/* ── Vue liste — structure de base ──────────────────────────────────── */
.fc-list-table {
  border-collapse: collapse;
}

/* Entête de jour */
.fc .fc-list-day-cushion {
  position: sticky;
  top: 0;
  z-index: 2;
  background-color: #f8fafc; /* slate-50 */
  border-bottom: 1px solid #f1f5f9; /* slate-100 */
  padding: 8px 12px;
}
.fc .fc-list-day-text,
.fc .fc-list-day-side-text {
  font-size: 0.8125rem;
  font-weight: 700;
  color: #334155; /* slate-700 */
  text-transform: capitalize;
  text-decoration: none;
}

/* Lignes d'événements */
.fc-list-event {
  @apply cursor-pointer;
}
.fc-list-event td {
  padding-top: 10px;
  padding-bottom: 10px;
  border-bottom: none !important;
  transition: background-color 150ms ease;
}
.fc-list-event:hover td {
  background-color: rgba(248, 250, 252, 0.6); /* slate-50/60 */
}

/* Colonne heure */
.fc .fc-list-event-time {
  font-size: 0.75rem;
  font-weight: 500;
  color: #64748b; /* slate-500 */
  min-width: 90px;
  background-color: transparent !important;
  white-space: nowrap;
}

/* Colonne dot */
.fc .fc-list-event-graphic {
  vertical-align: middle;
  padding-right: 6px;
}

/* Colonne titre */
.fc .fc-list-event-title a {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e293b; /* slate-800 */
  text-decoration: none;
  max-width: 260px;
  display: inline-block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Vue liste — suppression du dot natif FC (remplacé par mla-list-dot) ── */
.fc .fc-list-event-graphic {
  display: none;
}

/* ── Vue liste — eventContent enrichi ──────────────────────────────── */
.mla-list-event {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 3px 0;
  width: 100%;
}
.mla-list-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 3px;
}
.mla-list-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}
.mla-list-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.mla-list-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e293b; /* slate-800 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}
.mla-list-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
.mla-list-meta-chip {
  font-size: 0.6875rem;
  color: #64748b; /* slate-500 */
}
.mla-list-meta-sep {
  font-size: 0.6875rem;
  color: #cbd5e1; /* slate-300 */
}
.mla-list-status {
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: 999px;
  white-space: nowrap;
  flex-shrink: 0;
}
.mla-list-status--brouillon {
  background: #f1f5f9;
  color: #64748b;
}
.mla-list-status--publie {
  background: #dcfce7;
  color: #15803d;
}
.mla-list-status--annule {
  background: #fee2e2;
  color: #dc2626;
}
.mla-list-status--termine {
  background: #e2e8f0;
  color: #475569;
}

/* ── Indicateur "maintenant" ────────────────────────────────────────── */
.fc-timegrid-now-indicator-line {
  @apply border-primary-600;
}
</style>
