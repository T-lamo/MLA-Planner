import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usePagination } from '~~/layers/base/app/stores/utils/usePagination'
import { AffectationRepository } from '../repositories/AffectationRepository'
import type { AffectationMemberRead, AffectationStatus } from '../types/planning.types'

export const useMyAffectationsStore = defineStore('myAffectations', () => {
  const repo = new AffectationRepository()
  const notify = useMLANotify()

  const affectations = ref<AffectationMemberRead[]>([])
  const pendingCount = ref(0)
  const loading = ref(false)

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
  } = usePagination(20)

  async function fetchMyAffectations() {
    loading.value = true
    try {
      const res = await repo.getMyAffectations({
        limit: pagination.limit,
        offset: pagination.offset,
      })
      affectations.value = res.data
      setTotal(res.total)
    } finally {
      loading.value = false
    }
  }

  async function refreshPendingCount() {
    pendingCount.value = await repo.getPendingCount()
  }

  async function acceptAffectation(id: string) {
    await repo.updateMyStatus(id, 'CONFIRME')
    notify.success('Affectation acceptée')
    await fetchMyAffectations()
    await refreshPendingCount()
  }

  async function refuseAffectation(id: string) {
    await repo.updateMyStatus(id, 'REFUSE')
    notify.info('Affectation refusée')
    await fetchMyAffectations()
    await refreshPendingCount()
  }

  async function updateStatus(id: string, status: AffectationStatus) {
    await repo.updateStatus(id, status)
    notify.success('Statut mis à jour')
  }

  return {
    affectations,
    pendingCount,
    loading,
    pagination,
    total,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    goToPage,
    resetPagination,
    fetchMyAffectations,
    refreshPendingCount,
    acceptAffectation,
    refuseAffectation,
    updateStatus,
  }
})
