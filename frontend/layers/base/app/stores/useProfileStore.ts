// stores/useProfileStore.ts
import { defineStore } from 'pinia'
import { ref, reactive, watch } from 'vue'
import { useUIStore } from './useUiStore'
import type { ProfilReadFull, ProfilCreateFull, ProfilUpdateFull } from '../../types/profiles'
import { ProfileRepository } from '../repositories/ProfileRepository'
import { useMinistereStore } from './useMinistereStore'

export const useProfileStore = defineStore('profile', () => {
  const uiStore = useUIStore()
  const notify = useMLANotify()
  const ministereStore = useMinistereStore()

  const repository = new ProfileRepository()

  const profiles = ref<ProfilReadFull[]>([])
  const total = ref(0)
  const loading = ref(false)

  const pagination = reactive({
    limit: 10,
    offset: 0,
  })

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
        total.value = data.total
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
    total.value--

    try {
      // 3. Tentative de suppression côté serveur
      await repository.delete(id)

      // Succès : notification à l'utilisateur
      notify.success('Suppression', 'Membre retiré avec succès.')
    } catch {
      // 4. ÉCHEC : Rollback vers l'état précédent
      profiles.value = backupProfiles
      total.value = backupTotal

      // errors are handled by the global fetch interceptor
    }
  }

  watch(
    () => uiStore.selectedCampusId,
    () => {
      pagination.offset = 0
      fetchProfiles()
      ministereStore.fetchFullById('740ab849-699f-4c53-b08e-2e35096498ce')
    },
  )

  return {
    profiles,
    total,
    loading,
    pagination,
    fetchProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
  }
})
