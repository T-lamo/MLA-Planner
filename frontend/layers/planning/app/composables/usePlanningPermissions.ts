import { computed } from 'vue'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

/**
 * Source de vérité unique pour les droits de la couche planning.
 *
 * Délègue à useAuthStore.canManagePlanning — ne pas dupliquer la logique ici.
 * Ne jamais lire les noms de rôles directement dans ce composable.
 *
 * Utilisation : importer dans chaque composant planning qui a besoin de droits.
 */
export function usePlanningPermissions() {
  const authStore = useAuthStore()

  /** Peut créer, modifier, supprimer un planning et changer son statut. */
  const canWrite = computed<boolean>(() => authStore.can('PLANNING_WRITE'))

  /** Peut publier un planning (sous-ensemble de canWrite). */
  const canChangeStatus = computed<boolean>(() => authStore.can('PLANNING_PUBLISH'))

  /** Peut visualiser le calendrier (tout utilisateur authentifié). */
  const canViewCalendar = computed<boolean>(() => !!authStore.currentUser)

  return { canWrite, canChangeStatus, canViewCalendar }
}
