import type { CampusRead, CampusUpdate } from '../../types/campus'
import { useCampusStore } from '../stores/useCampusStore'

export const useCampuses = () => {
  const store = useCampusStore()
  const { items, total, loading, detailedMinisteres, detailedLoading, pagination } =
    storeToRefs(store)

  // Auto-fetch data when pagination changes
  watch(
    () => [pagination.value.limit, pagination.value.offset],
    () => store.fetchAll(),
    { deep: true },
  )

  /**
   * Utility: Prepares a CampusUpdate payload by stripping
   * read-only fields (id, relations, etc.)
   */
  const prepareUpdatePayload = (campus: CampusRead): CampusUpdate => {
    const { id, ...baseData } = campus
    // Explicitly return only mutable fields defined in CampusUpdate
    return {
      nom: baseData.nom,
      ville: baseData.ville,
      pays: baseData.pays ?? undefined,
      timezone: baseData.timezone,
      organisation_id: baseData.organisation_id,
    }
  }

  const changePage = (page: number) => {
    const newOffset = (page - 1) * pagination.value.limit
    store.setPagination(newOffset)
  }

  /**
   * Encapsulation de l'action de récupération détaillée.
   */
  const getDetailedMinisteres = async (campusId: string) => {
    return await store.fetchDetailedMinisteres(campusId)
  }

  return {
    // State
    campuses: items,
    totalCount: total,
    isLoading: loading,
    pagination,
    ministeresByCampus: detailedMinisteres,
    isDetailedLoading: detailedLoading,

    // Actions
    fetch: store.fetchAll,
    deleteCampus: store.remove,
    updateCampus: store.update,
    createCampus: store.create,
    fetchDetailedMinisteres: getDetailedMinisteres,
    // Logic Helpers
    changePage,
    prepareUpdatePayload,
  }
}
