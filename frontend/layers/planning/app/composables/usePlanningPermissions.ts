import { computed } from 'vue'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

/**
 * Source de vérité unique pour les droits de la couche planning.
 *
 * Règles :
 *  - canWrite   : RESPONSABLE_MLA, ADMIN, Super Admin → créer / modifier / supprimer / changer statut
 *  - canViewCalendar : tout utilisateur connecté → lecture seule
 *
 * Utilisation : importer dans chaque composant planning qui a besoin de droits.
 * Ne jamais dupliquer ces computed dans les templates.
 */
export function usePlanningPermissions() {
  const authStore = useAuthStore()

  /** Peut créer, modifier, supprimer un planning et changer son statut. */
  const canWrite = computed<boolean>(
    () =>
      authStore.hasAdminAccess ||
      (authStore.currentUser?.roles?.some((r) => r.toLowerCase().includes('responsable')) ?? false),
  )

  /** Peut changer le statut d'un planning (sous-ensemble de canWrite). */
  const canChangeStatus = computed<boolean>(() => canWrite.value)

  /** Peut visualiser le calendrier (tout utilisateur authentifié). */
  const canViewCalendar = computed<boolean>(() => !!authStore.currentUser)

  return { canWrite, canChangeStatus, canViewCalendar }
}
