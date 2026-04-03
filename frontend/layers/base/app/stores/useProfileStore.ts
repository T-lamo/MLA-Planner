// stores/useProfileStore.ts
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useUIStore } from './useUiStore'
import type { ProfilReadFull, ProfilCreateFull, ProfilUpdateFull } from '../../types/profiles'
import type { MinistereSimple } from '../../types/ministere'
import { ProfileRepository } from '../repositories/ProfileRepository'
import { usePagination } from './utils/usePagination'

export const useProfileStore = defineStore('profile', () => {
  const uiStore = useUIStore()
  const notify = useMLANotify()
  const repository = new ProfileRepository()

  const profiles = ref<ProfilReadFull[]>([])
  const loading = ref(false)
  const myMinisteres = ref<MinistereSimple[]>([])
  const profilesByMinistere = ref<Record<string, ProfilReadFull[]>>({})
  const loadingMinistere = ref(false)

  const {
    pagination,
    total,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    setTotal,
    goToPage,
    resetPagination,
  } = usePagination(50)

  async function fetchProfiles() {
    // 1. Sécurité : On s'assure d'avoir l'ID du campus
    if (!uiStore.selectedCampusId) return

    loading.value = true
    try {
      // 2. Appel du repository :
      // On passe l'ID en premier argument, et l'objet de pagination en second
      const data = await repository.getAllByCampus(uiStore.selectedCampusId, {
        limit: pagination.limit,
        offset: pagination.offset,
      })

      if (data) {
        profiles.value = data.data
        setTotal(data.total)
      }
    } catch {
      // errors are handled by the global fetch interceptor
    } finally {
      loading.value = false
    }
  }

  async function createProfile(payload: ProfilCreateFull) {
    loading.value = true
    try {
      const data = await repository.create(payload)
      if (data) {
        notify.success('Création réussie', `Le profil ${data.nom} a été ajouté.`)
        await fetchProfiles()
      }
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(id: string, payload: ProfilUpdateFull) {
    loading.value = true
    try {
      const data = await repository.update(id, payload)
      if (data) {
        notify.success('Mise à jour réussie', `Le profil ${data.nom} a été modifié.`)
        const index = profiles.value.findIndex((p) => p.id === id)
        if (index !== -1) profiles.value[index] = data
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Orchestre la suppression (Optimiste avec Try/Catch)
   */
  async function deleteProfile(id: string) {
    // 1. Sauvegarde de l'état (Backup) pour le Rollback
    const backupProfiles = [...profiles.value]
    const backupTotal = total.value

    // 2. Mise à jour optimiste immédiate (Interface fluide)
    profiles.value = profiles.value.filter((p) => p.id !== id)
    setTotal(backupTotal - 1)

    try {
      // 3. Tentative de suppression côté serveur
      await repository.delete(id)

      // Succès : notification à l'utilisateur
      notify.success('Suppression', 'Membre retiré avec succès.')
    } catch {
      // 4. ÉCHEC : Rollback vers l'état précédent
      profiles.value = backupProfiles
      setTotal(backupTotal)

      // errors are handled by the global fetch interceptor
    }
  }

  async function fetchMyMinisteres(campusId: string) {
    try {
      myMinisteres.value = await repository.getMyMinisteresByCampus(campusId)
    } catch {
      // errors handled globally
    }
  }

  function clearMinistereCache() {
    profilesByMinistere.value = {}
    myMinisteres.value = []
  }

  async function fetchProfilesByMinistere(ministereId: string, campusId: string) {
    const cacheKey = `${campusId}:${ministereId}`
    loadingMinistere.value = true
    try {
      profilesByMinistere.value[cacheKey] = await repository.getAllByMinistere(
        ministereId,
        campusId,
      )
    } catch {
      // errors handled globally
    } finally {
      loadingMinistere.value = false
    }
  }

  watch(
    () => uiStore.selectedCampusId,
    () => {
      resetPagination()
      fetchProfiles()
    },
    { immediate: true },
  )

  return {
    profiles,
    total,
    loading,
    myMinisteres,
    profilesByMinistere,
    loadingMinistere,
    pagination,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    goToPage,
    resetPagination,
    fetchProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    fetchMyMinisteres,
    fetchProfilesByMinistere,
    clearMinistereCache,
  }
})
