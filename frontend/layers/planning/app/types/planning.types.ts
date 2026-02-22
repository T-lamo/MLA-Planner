import type { EventInput } from '@fullcalendar/core'

export type PlanningStatus = 'BROUILLON' | 'VALIDÉ' | 'ARCHIVÉ'
export type PlanningViewPerspective = 'PERSONAL' | 'MINISTERE' | 'CAMPUS'

export interface PlanningEventMetadata {
  campus: string
  ministereId: string
  ministereLabel: string
  typeActivite: string
  statut: PlanningStatus
  membreIds: string[]
  responsableId: string
}

export interface PlanningEvent extends EventInput {
  id: string
  title: string
  start: string
  end?: string
  allDay?: boolean
  // Utilisation de extendedProps pour respecter la structure FullCalendar
  extendedProps: PlanningEventMetadata
}
