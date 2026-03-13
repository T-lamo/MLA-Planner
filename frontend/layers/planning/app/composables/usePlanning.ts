import { ref, computed, watch } from 'vue'
import type { EnhancedApiError } from '~~/layers/base/types/api'
import type {
  CampusFilterParams,
  MinistereColor,
  PlanningEvent,
  PlanningFullRead,
  PlanningViewPerspective,
} from '../types/planning.types'
import { getMinistereColor } from '../types/planning.types'
import { PlanningRepository } from '../repositories/PlanningRepository'
import { ProfileRepository } from '~~/layers/base/app/repositories/ProfileRepository'
import type { ProfilReadFull } from '~~/layers/base/types/profiles'
import type { CampusRead } from '~~/layers/base/types/campus'
import type { MinistereSimple } from '~~/layers/base/types/ministere'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { useUIStore } from '~~/layers/base/app/stores/useUiStore'

export const usePlanning = () => {
  const authStore = useAuthStore()
  const uiStore = useUIStore()
  const planningRepo = new PlanningRepository()
  const profileRepo = new ProfileRepository()
  const { notifyError } = useErrorHandler()

  // -----------------------------------------------------------------------
  // État
  // -----------------------------------------------------------------------

  const perspective = ref<PlanningViewPerspective>('PERSONAL')
  const activeMinistereId = ref<string | null>(null)
  const rawPlannings = ref<PlanningFullRead[]>([])
  const myProfile = ref<ProfilReadFull | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // -----------------------------------------------------------------------
  // Dérivés du profil
  // -----------------------------------------------------------------------

  const ministeres = computed<MinistereSimple[]>(() => myProfile.value?.ministeres ?? [])
  const ministereIds = computed<string[]>(() => ministeres.value.map((m) => m.id))
  const currentMembreId = computed<string | null>(() => authStore.currentUser?.membreId ?? null)
  const userCampuses = computed<CampusRead[]>(() => myProfile.value?.campuses ?? [])
  const userCampusPrincipalId = computed<string | null>(
    () => myProfile.value?.campus_principal_id ?? null,
  )

  // -----------------------------------------------------------------------
  // Couleurs par ministère (attribution déterministe par position)
  // -----------------------------------------------------------------------

  const ministereColorMap = computed<Map<string, MinistereColor>>(() => {
    const map = new Map<string, MinistereColor>()
    ministereIds.value.forEach((id) => {
      map.set(id, getMinistereColor(id, ministereIds.value))
    })
    return map
  })

  // -----------------------------------------------------------------------
  // Transformation PlanningFullRead → PlanningEvent (FullCalendar)
  // -----------------------------------------------------------------------

  function toCalendarEvent(planning: PlanningFullRead): PlanningEvent {
    const ministereId = planning.activite?.ministere_organisateur_id ?? ''
    const ministereLabel =
      ministeres.value.find((m) => m.id === ministereId)?.nom ??
      planning.activite?.ministere_organisateur_nom ??
      ministereId
    const color: MinistereColor =
      ministereColorMap.value.get(ministereId) ?? getMinistereColor(ministereId, ministereIds.value)

    const allAffectations = planning.slots.flatMap((s) => s.affectations)

    const membreIds = allAffectations.map((a) => a.membre?.id ?? '').filter(Boolean)

    const membres = allAffectations
      .filter((a): a is typeof a & { membre: NonNullable<typeof a.membre> } => a.membre != null)
      .map((a) => ({ id: a.membre.id, prenom: a.membre.prenom, nom: a.membre.nom }))
      .filter((m, idx, arr) => arr.findIndex((x) => x.id === m.id) === idx)

    const isPersonal =
      perspective.value === 'PERSONAL' ||
      (currentMembreId.value !== null && membreIds.includes(currentMembreId.value))

    return {
      id: planning.id,
      title: planning.activite?.type ?? 'Activité',
      start: planning.activite?.date_debut ?? '',
      end: planning.activite?.date_fin,
      backgroundColor: color.bg,
      borderColor: color.border,
      textColor: color.text,
      extendedProps: {
        campus:
          planning.activite?.campus_nom ??
          userCampuses.value.find((c) => c.id === planning.activite?.campus_id)?.nom ??
          planning.activite?.campus_id ??
          '',
        ministereId,
        ministereLabel,
        typeActivite: planning.activite?.type ?? '',
        statut: planning.statut_code,
        membreIds,
        membres,
        responsableId: '',
        isPersonal,
        ministereColor: color,
      },
    }
  }

  const events = computed<PlanningEvent[]>(() => rawPlannings.value.map(toCalendarEvent))

  // -----------------------------------------------------------------------
  // Chargement du profil courant (lazy — une seule fois par instance)
  // -----------------------------------------------------------------------

  async function ensureProfile(): Promise<void> {
    if (myProfile.value) return
    myProfile.value = await profileRepo.getMyProfile()
  }

  // -----------------------------------------------------------------------
  // Déduplique en cas d'union de plusieurs ministères
  // -----------------------------------------------------------------------

  function deduplicatePlannings(plannings: PlanningFullRead[]): PlanningFullRead[] {
    const seen = new Set<string>()
    return plannings.filter((p) => {
      if (seen.has(p.id)) return false
      seen.add(p.id)
      return true
    })
  }

  // -----------------------------------------------------------------------
  // Chargement principal — déclenché par perspective + ministère actif
  // -----------------------------------------------------------------------

  async function refresh(): Promise<void> {
    if (!authStore.isAuthenticated) return
    if (isLoading.value) return
    isLoading.value = true
    error.value = null

    try {
      await ensureProfile()

      const campusId = uiStore.selectedCampusId || undefined

      if (perspective.value === 'PERSONAL') {
        rawPlannings.value = await planningRepo.listMyCalendar(campusId)
      } else if (perspective.value === 'MINISTERE') {
        if (activeMinistereId.value) {
          rawPlannings.value = await planningRepo.listByMinistere(activeMinistereId.value, campusId)
        } else {
          // Aucun ministère actif → union de tous les ministères de l'utilisateur
          const results = await Promise.all(
            ministereIds.value.map((id) => planningRepo.listByMinistere(id, campusId)),
          )
          rawPlannings.value = deduplicatePlannings(results.flat())
        }
      } else {
        // CAMPUS — utilise le campus sélectionné dans la navbar
        if (!uiStore.selectedCampusId) {
          error.value = 'Aucun campus sélectionné.'
          rawPlannings.value = []
          return
        }
        rawPlannings.value = await planningRepo.listByCampus(uiStore.selectedCampusId)
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur lors du chargement du planning'
      notifyError(e as EnhancedApiError)
    } finally {
      isLoading.value = false
    }
  }

  // -----------------------------------------------------------------------
  // Actions publiques
  // -----------------------------------------------------------------------

  function setView(v: PlanningViewPerspective): void {
    perspective.value = v
  }

  function setMinistere(id: string | null): void {
    activeMinistereId.value = id
  }

  /**
   * Mise à jour optimiste d'un planning en place (après PATCH status ou edit).
   * Évite un refetch complet et le clignotement du calendrier.
   */
  function patchLocalPlanning(updated: PlanningFullRead): void {
    const idx = rawPlannings.value.findIndex((p) => p.id === updated.id)
    if (idx === -1) return
    const existing = rawPlannings.value[idx]!
    const patched = {
      ...updated,
      activite: updated.activite ?? existing.activite,
    }
    rawPlannings.value = rawPlannings.value.map((p, i) => (i === idx ? patched : p))
  }

  /** Supprime un planning du cache local (après DELETE). */
  function removeLocalPlanning(id: string): void {
    rawPlannings.value = rawPlannings.value.filter((p) => p.id !== id)
  }

  // Auto-refresh when perspective, active ministère or selected campus changes
  watch([perspective, activeMinistereId, () => uiStore.selectedCampusId], () => {
    refresh()
  })

  // -----------------------------------------------------------------------
  // API publique du composable
  // -----------------------------------------------------------------------

  return {
    // État réactif
    perspective,
    activeMinistereId,
    isLoading,
    error,
    rawPlannings,

    // Dérivés
    ministeres,
    ministereIds,
    ministereColorMap,
    events,
    userCampuses,
    userCampusPrincipalId,

    // Filtres campus (pour MLA-PLAN-09)
    campusFilters: ref<CampusFilterParams>({}),

    // Actions
    setView,
    setMinistere,
    refresh,
    patchLocalPlanning,
    removeLocalPlanning,
  }
}
