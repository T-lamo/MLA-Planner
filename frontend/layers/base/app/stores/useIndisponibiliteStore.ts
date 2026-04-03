// stores/useIndisponibiliteStore.ts
import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'
import type {
  IndisponibiliteCreate,
  IndisponibiliteFilters,
  IndisponibiliteReadFull,
} from '../../types/indisponibilites'
import { IndisponibiliteRepository } from '../repositories/IndisponibiliteRepository'
import { usePagination } from './utils/usePagination'

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

  // Deux paginations indépendantes : membre vs admin
  const paginationMine = usePagination(20)
  const paginationAdmin = usePagination(20)

  // -----------------------------------------------------------------------
  // Actions membre
  // -----------------------------------------------------------------------

  async function fetchMine(): Promise<void> {
    loading.value = true
    try {
      const res = await repo.getMyIndisponibilites({
        limit: paginationMine.pagination.limit,
        offset: paginationMine.pagination.offset,
      })
      myIndisponibilites.value = res.data
      paginationMine.setTotal(res.total)
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
      const res = await repo.getByCampus(
        campusId,
        {
          ministere_id: filters.ministere_id,
          date_debut: filters.date_debut,
          date_fin: filters.date_fin,
          validee_only: filters.validee_only,
        },
        {
          limit: paginationAdmin.pagination.limit,
          offset: paginationAdmin.pagination.offset,
        },
      )
      adminIndisponibilites.value = res.data
      paginationAdmin.setTotal(res.total)
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
    paginationMine,
    paginationAdmin,
    fetchMine,
    declare,
    remove,
    fetchByCampus,
    valider,
    adminRemove,
  }
})
