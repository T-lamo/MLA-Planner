// stores/useIndisponibiliteStore.ts
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import type {
  IndisponibiliteCreate,
  IndisponibiliteFilters,
  IndisponibiliteReadFull,
} from '../../types/indisponibilites'
import { IndisponibiliteRepository } from '../repositories/IndisponibiliteRepository'

export const useIndisponibiliteStore = defineStore('indisponibilite', () => {
  const repo = new IndisponibiliteRepository()
  const notify = useMLANotify()

  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------
  const myIndisponibilites = ref<IndisponibiliteReadFull[]>([])
  const adminIndisponibilites = ref<IndisponibiliteReadFull[]>([])
  const loading = ref(false)

  const filters = reactive<IndisponibiliteFilters>({
    ministere_id: undefined,
    date_debut: undefined,
    date_fin: undefined,
    validee_only: false,
  })

  // -----------------------------------------------------------------------
  // Actions membre
  // -----------------------------------------------------------------------

  async function fetchMine(): Promise<void> {
    loading.value = true
    try {
      myIndisponibilites.value = await repo.getMyIndisponibilites()
    } catch {
      // handled by global interceptor
    } finally {
      loading.value = false
    }
  }

  async function declare(payload: IndisponibiliteCreate): Promise<void> {
    loading.value = true
    try {
      await repo.create(payload)
      await fetchMine()
      notify.success('Déclaration enregistrée', 'En attente de validation.')
    } catch {
      // handled by global interceptor
    } finally {
      loading.value = false
    }
  }

  async function remove(id: string): Promise<void> {
    const backup = [...myIndisponibilites.value]
    myIndisponibilites.value = myIndisponibilites.value.filter((i) => i.id !== id)
    try {
      await repo.delete(id)
      notify.success('Supprimée', 'Indisponibilité retirée.')
    } catch {
      myIndisponibilites.value = backup
    }
  }

  // -----------------------------------------------------------------------
  // Actions admin
  // -----------------------------------------------------------------------

  async function fetchByCampus(campusId: string): Promise<void> {
    loading.value = true
    try {
      adminIndisponibilites.value = await repo.getByCampus(campusId, {
        ministere_id: filters.ministere_id,
        date_debut: filters.date_debut,
        date_fin: filters.date_fin,
        validee_only: filters.validee_only,
      })
    } catch {
      // handled by global interceptor
    } finally {
      loading.value = false
    }
  }

  async function valider(id: string): Promise<void> {
    const idx = adminIndisponibilites.value.findIndex((i) => i.id === id)
    const item = idx !== -1 ? adminIndisponibilites.value[idx] : undefined
    const backup = item ? { ...item } : null
    if (idx !== -1 && item) {
      adminIndisponibilites.value[idx] = { ...item, validee: true }
    }
    try {
      const updated = await repo.valider(id)
      if (idx !== -1) adminIndisponibilites.value[idx] = updated
      notify.success('Validée', 'Indisponibilité confirmée.')
    } catch {
      if (idx !== -1 && backup) adminIndisponibilites.value[idx] = backup
    }
  }

  async function adminRemove(id: string): Promise<void> {
    const backup = [...adminIndisponibilites.value]
    adminIndisponibilites.value = adminIndisponibilites.value.filter((i) => i.id !== id)
    try {
      await repo.adminDelete(id)
      notify.success('Supprimée', 'Indisponibilité supprimée.')
    } catch {
      adminIndisponibilites.value = backup
    }
  }

  // -----------------------------------------------------------------------
  // Computed helpers
  // -----------------------------------------------------------------------

  const pendingCount = computed(() => adminIndisponibilites.value.filter((i) => !i.validee).length)

  return {
    myIndisponibilites,
    adminIndisponibilites,
    loading,
    filters,
    pendingCount,
    fetchMine,
    declare,
    remove,
    fetchByCampus,
    valider,
    adminRemove,
  }
})
