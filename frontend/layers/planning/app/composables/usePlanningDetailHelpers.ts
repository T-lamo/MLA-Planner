import { computed, type ComputedRef, type InjectionKey, type Ref } from 'vue'
import type {
  AffectationFullRead,
  CampusTeamRead,
  MinistereColor,
  PlanningEvent,
  PlanningFullRead,
  RoleCompetenceRead,
} from '../types/planning.types'
import type { useUIStore } from '~~/layers/base/app/stores/useUiStore'

/**
 * Fonction pure utilitaire — recherche le ministère d'un membre dans une équipe campus.
 * Exportée pour être réutilisée dans d'autres composables (ex : usePlanningForm.initForm).
 */
export function findMinistreForMembreInTeam(
  campusTeam: CampusTeamRead | null,
  membreId: string,
): string {
  if (!campusTeam) return ''
  for (const min of campusTeam.ministeres) {
    if (min.membres.some((m) => m.id === membreId)) return min.id
  }
  return ''
}

export type PlanningDetailHelpers = ReturnType<typeof usePlanningDetailHelpers>
export const planningDetailHelpersKey: InjectionKey<PlanningDetailHelpers> =
  Symbol('planningDetailHelpers')

export function usePlanningDetailHelpers(
  planning: Ref<PlanningFullRead | null | undefined>,
  planningEvent: Ref<PlanningEvent | null | undefined>,
  campusTeam: Ref<CampusTeamRead | null>,
  roles: Ref<RoleCompetenceRead[]>,
  campusMinistereColorMap: ComputedRef<Map<string, MinistereColor>>,
  ministereColorMap: ComputedRef<Map<string, MinistereColor>>,
  uiStore: ReturnType<typeof useUIStore>,
) {
  // -----------------------------------------------------------------------
  // Computed — contexte organisationnel
  // -----------------------------------------------------------------------
  const detailCampusNom = computed<string>(() => {
    const nom = planning.value?.activite?.campus_nom
    if (nom) return nom
    const campusId = planning.value?.activite?.campus_id
    if (campusId) return uiStore.myCampuses.find((c) => c.id === campusId)?.nom ?? campusId
    return ''
  })

  const detailMinistereNom = computed<string>(
    () =>
      planning.value?.activite?.ministere_organisateur_nom ??
      planningEvent.value?.extendedProps.ministereLabel ??
      '',
  )

  const detailMinistreColor = computed(() => {
    const id =
      planning.value?.activite?.ministere_organisateur_id ??
      planningEvent.value?.extendedProps.ministereId ??
      ''
    return campusMinistereColorMap.value.get(id) ?? ministereColorMap.value.get(id) ?? null
  })

  // -----------------------------------------------------------------------
  // Computed — statistiques créneaux / équipe
  // -----------------------------------------------------------------------
  const totalMembresUniques = computed<number>(() => {
    const ids = new Set<string>()
    for (const slot of planning.value?.slots ?? []) {
      for (const aff of slot.affectations) {
        if (aff.membre?.id) ids.add(aff.membre.id)
      }
    }
    return ids.size
  })

  const globalFillRate = computed<number>(() => {
    const slots = planning.value?.slots ?? []
    if (!slots.length) return 0
    const sum = slots.reduce((acc, sl) => acc + sl.filling_rate, 0)
    return Math.round(sum / slots.length)
  })

  // -----------------------------------------------------------------------
  // Helpers — résolution ministère / affectation
  // -----------------------------------------------------------------------
  function findMinistreForMembre(membreId: string): string {
    return findMinistreForMembreInTeam(campusTeam.value, membreId)
  }

  function ministreNomForMembre(membreId: string): string {
    if (!campusTeam.value) return ''
    const min = campusTeam.value.ministeres.find((m) => m.membres.some((mb) => mb.id === membreId))
    return min?.nom ?? ''
  }

  function ministreColorForMembre(membreId: string): MinistereColor | null {
    const ministreId = findMinistreForMembre(membreId)
    if (!ministreId) return null
    return campusMinistereColorMap.value.get(ministreId) ?? null
  }

  function ministreNomForAff(aff: AffectationFullRead): string {
    if (aff.ministere_nom) return aff.ministere_nom
    if (aff.membre?.id) return ministreNomForMembre(aff.membre.id)
    return ''
  }

  function ministreColorForAff(aff: AffectationFullRead): MinistereColor | null {
    if (aff.ministere_id) {
      return campusMinistereColorMap.value.get(aff.ministere_id) ?? null
    }
    if (aff.membre?.id) return ministreColorForMembre(aff.membre.id)
    return null
  }

  // -----------------------------------------------------------------------
  // Helpers — rôles / statuts affectation
  // -----------------------------------------------------------------------
  function roleLibelle(roleCode: string): string {
    return roles.value.find((r) => r.code === roleCode)?.libelle ?? roleCode
  }

  function affStatusBadge(code: string): string {
    if (code === 'CONFIRME')
      return 'rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-700'
    if (code === 'REFUSE')
      return 'rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-600'
    if (code === 'PRESENT')
      return 'rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold text-blue-700'
    return 'rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700'
  }

  function affStatusLabel(code: string): string {
    const labels: Record<string, string> = {
      PROPOSE: 'Proposé',
      CONFIRME: 'Confirmé',
      REFUSE: 'Refusé',
      PRESENT: 'Présent',
    }
    return labels[code] ?? code
  }

  // -----------------------------------------------------------------------
  // Formatage dates
  // -----------------------------------------------------------------------
  const formatDate = (date: string) =>
    new Date(date).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })

  const formatTime = (date?: string) =>
    date
      ? new Date(date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      : '--:--'

  return {
    detailCampusNom,
    detailMinistereNom,
    detailMinistreColor,
    totalMembresUniques,
    globalFillRate,
    findMinistreForMembre,
    ministreNomForMembre,
    ministreColorForMembre,
    ministreNomForAff,
    ministreColorForAff,
    roleLibelle,
    affStatusBadge,
    affStatusLabel,
    formatDate,
    formatTime,
  }
}
