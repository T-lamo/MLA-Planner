import { defineStore } from 'pinia'
import { MinistereRepository } from '../repositories/MinistereRepository'
import { usePagination } from './utils/usePagination' // Import du composable mutualisé
import type {
  MinistereCreate,
  MinistereRead,
  MinistereReadWithRelations,
  MinistereUpdate,
} from '../../types/ministere'

export const useMinistereStore = defineStore('ministere', () => {
  const repository = new MinistereRepository()

  // Utilisation du composable (par défaut limit: 10)
  const { pagination, setPagination, resetPagination } = usePagination(10)

  // --- State ---
  const items = ref<MinistereRead[]>([])
  const currentMinistere = ref<MinistereReadWithRelations | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const error = ref<unknown>(null)

  // --- Actions ---

  /**
   * Récupère la liste paginée
   */
  async function fetchAll(params: Record<string, unknown> = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await repository.getAll({
        limit: pagination.limit,
        offset: pagination.offset,
        ...params,
      })
      items.value = response.data
      total.value = response.total
    } catch (e) {
      error.value = e
      throw e
    } finally {
      loading.value = false
    }
  }

  /**
   * Récupère le détail complet (relations incluses)
   */
  async function fetchFullById(id: string) {
    loading.value = true
    error.value = null
    try {
      const data = await repository.getFullById(id)
      currentMinistere.value = data
      return data
    } catch (e) {
      error.value = e
      currentMinistere.value = null
      throw e
    } finally {
      loading.value = false
    }
  }

  async function create(payload: MinistereCreate) {
    loading.value = true
    try {
      const newItem = await repository.create(payload)
      // On reset la pagination pour voir le nouvel élément (souvent en début de liste)
      resetPagination()
      await fetchAll()
      return newItem
    } finally {
      loading.value = false
    }
  }

  async function update(id: string, payload: MinistereUpdate) {
    loading.value = true
    try {
      const updated = await repository.update(id, payload)

      // Mise à jour dans la liste locale
      const index = items.value.findIndex((m) => m.id === id)
      if (index !== -1) items.value[index] = updated

      // Si on modifie le ministère actuellement visualisé, on rafraîchit ses relations
      if (currentMinistere.value?.id === id) {
        await fetchFullById(id)
      }
      return updated
    } finally {
      loading.value = false
    }
  }

  /**
   * Suppression optimiste avec rollback
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

  function resetCurrent() {
    currentMinistere.value = null
  }

  return {
    // State & Pagination
    items,
    currentMinistere,
    total,
    loading,
    error,
    pagination,

    // Actions
    fetchAll,
    fetchFullById,
    create,
    update,
    remove,
    resetCurrent,
    setPagination,
    resetPagination,
  }
})
