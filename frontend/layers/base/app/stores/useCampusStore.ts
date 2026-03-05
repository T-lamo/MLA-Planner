import { defineStore } from 'pinia'
import { CampusRepository } from '../repositories/CampusRepository'
import { usePagination } from './utils/usePagination' // Adaptez le chemin d'import
import type { CampusCreate, CampusRead, CampusUpdate } from '../../types/campus'
import type { MinistereReadWithRelations } from '../../types/ministere'

export const useCampusStore = defineStore('campus', () => {
  const repository = new CampusRepository()

  // Utilisation du composable mutualisé
  const { pagination, setPagination, resetPagination } = usePagination(10)

  // --- State ---
  const items = ref<CampusRead[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<unknown>(null)
  const detailedMinisteres = ref<MinistereReadWithRelations[]>([])
  const detailedLoading = ref(false)

  // --- Getters ---
  const getById = computed(() => (id: string) => items.value.find((c) => c.id === id))

  // --- Actions ---

  /**
   * Récupère la liste en injectant l'état de pagination actuel
   */
  async function fetchAll(params: Record<string, unknown> = {}) {
    loading.value = true
    error.value = null
    try {
      const data = await repository.getAll({
        limit: pagination.limit,
        offset: pagination.offset,
        ...params,
      })
      items.value = data.data
      total.value = data.total
    } catch (e: unknown) {
      error.value = e
      throw e
    } finally {
      loading.value = false
    }
  }

  async function create(payload: CampusCreate) {
    loading.value = true
    try {
      const newItem = await repository.create(payload)
      // On repart souvent à l'offset 0 pour voir le nouvel élément
      resetPagination()
      await fetchAll()
      return newItem
    } finally {
      loading.value = false
    }
  }

  async function update(id: string, payload: CampusUpdate) {
    loading.value = true
    try {
      const updated = await repository.update(id, payload)
      const index = items.value.findIndex((item) => item.id === id)
      if (index !== -1) items.value[index] = updated
      return updated
    } finally {
      loading.value = false
    }
  }

  /**
   * Optimistic Delete with Full Rollback
   */
  async function remove(id: string) {
    const previousItems = [...items.value]
    const previousTotal = total.value

    items.value = items.value.filter((item) => item.id !== id)
    total.value--

    try {
      await repository.delete(id)
    } catch (e) {
      items.value = previousItems
      total.value = previousTotal
      error.value = e
      throw e
    }
  }

  /**
   * Action d'orchestration pour la vue détaillée des ministères.
   * Gère son propre état de chargement pour une UI fluide.
   */
  async function fetchDetailedMinisteres(campusId: string): Promise<MinistereReadWithRelations[]> {
    detailedLoading.value = true
    error.value = null
    try {
      const data = await repository.getDetailedMinisteres(campusId)
      detailedMinisteres.value = data
      return data
    } catch (e: unknown) {
      error.value = e
      throw e
    } finally {
      detailedLoading.value = false
    }
  }

  return {
    // State & Composable state
    items,
    total,
    loading,
    error,
    pagination,
    detailedMinisteres,
    detailedLoading,
    // Getters
    getById,
    // Actions
    fetchAll,
    create,
    update,
    remove,
    setPagination,
    resetPagination,
    fetchDetailedMinisteres,
  }
})
