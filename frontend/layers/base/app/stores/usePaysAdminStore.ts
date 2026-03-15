import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { PaysCreate, PaysRead, PaysUpdate } from '../../types/pays'
import { PaysRepository } from '../repositories/PaysRepository'

export const usePaysAdminStore = defineStore('pays-admin', () => {
  const notify = useMLANotify()
  const repository = new PaysRepository()

  const pays = ref<PaysRead[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchAllPays() {
    loading.value = true
    try {
      const data = await repository.getAllPays()
      pays.value = data
      total.value = data.length
    } catch {
      // errors handled by global fetch interceptor
    } finally {
      loading.value = false
    }
  }

  async function createPays(payload: PaysCreate) {
    loading.value = true
    try {
      const data = await repository.create(payload)
      if (data) {
        notify.success('Création réussie', `Le pays ${data.nom} a été ajouté.`)
        await fetchAllPays()
      }
    } finally {
      loading.value = false
    }
  }

  async function updatePays(id: string, payload: PaysUpdate) {
    loading.value = true
    try {
      const data = await repository.update(id, payload)
      if (data) {
        notify.success('Mise à jour réussie', `Le pays ${data.nom} a été modifié.`)
        const index = pays.value.findIndex((p) => p.id === id)
        if (index !== -1) pays.value[index] = data
      }
    } finally {
      loading.value = false
    }
  }

  async function deletePays(id: string) {
    const backup = [...pays.value]
    const backupTotal = total.value

    pays.value = pays.value.filter((p) => p.id !== id)
    total.value--

    try {
      await repository.delete(id)
      notify.success('Suppression', 'Pays supprimé avec succès.')
    } catch {
      pays.value = backup
      total.value = backupTotal
      // errors handled by global fetch interceptor
    }
  }

  return {
    pays,
    loading,
    total,
    fetchAllPays,
    createPays,
    updatePays,
    deletePays,
  }
})
