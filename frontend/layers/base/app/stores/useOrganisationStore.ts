import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  OrganisationCreate,
  OrganisationRead,
  OrganisationUpdate,
} from '../../types/organisation'
import { OrganisationRepository } from '../repositories/OrganisationRepository'

export const useOrganisationStore = defineStore('organisation', () => {
  const notify = useMLANotify()
  const repository = new OrganisationRepository()

  const organisations = ref<OrganisationRead[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchOrganisations() {
    loading.value = true
    try {
      const data = await repository.getAllOrganisations()
      organisations.value = data
      total.value = data.length
    } catch {
      // errors handled by global fetch interceptor
    } finally {
      loading.value = false
    }
  }

  async function createOrganisation(payload: OrganisationCreate) {
    loading.value = true
    try {
      const data = await repository.create(payload)
      if (data) {
        notify.success('Création réussie', `L'organisation ${data.nom} a été ajoutée.`)
        await fetchOrganisations()
      }
    } finally {
      loading.value = false
    }
  }

  async function updateOrganisation(id: string, payload: OrganisationUpdate) {
    loading.value = true
    try {
      const data = await repository.update(id, payload)
      if (data) {
        notify.success('Mise à jour réussie', `L'organisation ${data.nom} a été modifiée.`)
        const index = organisations.value.findIndex((o) => o.id === id)
        if (index !== -1) organisations.value[index] = data
      }
    } finally {
      loading.value = false
    }
  }

  async function deleteOrganisation(id: string) {
    const backup = [...organisations.value]
    const backupTotal = total.value

    organisations.value = organisations.value.filter((o) => o.id !== id)
    total.value--

    try {
      await repository.delete(id)
      notify.success('Suppression', 'Organisation supprimée avec succès.')
    } catch {
      organisations.value = backup
      total.value = backupTotal
      // errors handled by global fetch interceptor
    }
  }

  return {
    organisations,
    loading,
    total,
    fetchOrganisations,
    createOrganisation,
    updateOrganisation,
    deleteOrganisation,
  }
})
