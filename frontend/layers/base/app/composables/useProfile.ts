import { useProfileStore } from '../stores/useProfileStore'
import { useUIStore } from '../stores/useUiStore'
import type { ProfilCreateFull } from '../../types/profiles'

// composables/useProfiles.ts
export const useProfiles = () => {
  const profileStore = useProfileStore()
  const uiStore = useUIStore()

  // On expose uniquement ce qui est nécessaire au composant
  const profiles = computed(() => profileStore.profiles)
  const isFetching = computed(() => profileStore.loading)
  const totalProfiles = computed(() => profileStore.total)

  // Proxy pour le changement de campus (facilite le v-model dans le header)
  const activeCampusId = computed({
    get: () => uiStore.selectedCampusId,
    set: (val) => (uiStore.selectedCampusId = val),
  })

  const handleCreate = async (data: ProfilCreateFull) => {
    await profileStore.createProfile(data)
  }

  const handleDelete = async (id: string) => {
    // Possibilité d'ajouter une confirmation ici via un autre store UI
    await profileStore.deleteProfile(id)
  }

  return {
    profiles,
    isFetching,
    totalProfiles,
    activeCampusId,
    campuses: computed(() => uiStore.campuses),
    refresh: profileStore.fetchProfiles,
    create: handleCreate,
    remove: handleDelete,
  }
}
