import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CampusCreate, CampusRead, CampusUpdate } from '../../types/campus'
import { CampusRepository } from '../repositories/CampusRepository'

export const useCampusAdminStore = defineStore('campusAdmin', () => {
  const notify = useMLANotify()
  const repository = new CampusRepository()

  const allCampuses = ref<CampusRead[]>([])
  const loading = ref(false)

  async function fetchAllCampuses() {
    loading.value = true
    try {
      const data = await repository.getAllCampuses()
      allCampuses.value = data
    } catch {
      // errors handled by global fetch interceptor
    } finally {
      loading.value = false
    }
  }

  async function createCampus(payload: CampusCreate) {
    loading.value = true
    try {
      const data = await repository.create(payload)
      if (data) {
        notify.success('Création réussie', `Le campus ${data.nom} a été ajouté.`)
        await fetchAllCampuses()
      }
    } finally {
      loading.value = false
    }
  }

  async function updateCampus(id: string, payload: CampusUpdate) {
    loading.value = true
    try {
      const data = await repository.update(id, payload)
      if (data) {
        notify.success('Mise à jour réussie', `Le campus ${data.nom} a été modifié.`)
        const index = allCampuses.value.findIndex((c) => c.id === id)
        if (index !== -1) allCampuses.value[index] = data
      }
    } finally {
      loading.value = false
    }
  }

  async function deleteCampus(id: string) {
    const backup = [...allCampuses.value]

    allCampuses.value = allCampuses.value.filter((c) => c.id !== id)

    try {
      await repository.delete(id)
      notify.success('Suppression', 'Campus supprimé avec succès.')
    } catch {
      allCampuses.value = backup
      // errors handled by global fetch interceptor
    }
  }

  return {
    allCampuses,
    loading,
    fetchAllCampuses,
    createCampus,
    updateCampus,
    deleteCampus,
  }
})
