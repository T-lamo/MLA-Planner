import { computed, reactive, ref } from 'vue'

export function usePagination(defaultLimit = 20) {
  const pagination = reactive({
    limit: defaultLimit,
    offset: 0,
  })

  const total = ref<number>(0)

  const currentPage = computed<number>(() => Math.floor(pagination.offset / pagination.limit) + 1)

  const totalPages = computed<number>(() => Math.ceil(total.value / pagination.limit) || 1)

  const hasNext = computed<boolean>(() => currentPage.value < totalPages.value)

  const hasPrev = computed<boolean>(() => currentPage.value > 1)

  function setTotal(n: number): void {
    total.value = n
  }

  function goToPage(page: number): void {
    const clamped = Math.max(1, Math.min(page, totalPages.value))
    pagination.offset = (clamped - 1) * pagination.limit
  }

  function setPagination(offset: number, limit?: number): void {
    pagination.offset = offset
    if (limit) pagination.limit = limit
  }

  function resetPagination(): void {
    pagination.offset = 0
    pagination.limit = defaultLimit
    total.value = 0
  }

  return {
    pagination,
    total,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    setTotal,
    goToPage,
    setPagination,
    resetPagination,
  }
}

export type PaginationState = ReturnType<typeof usePagination>
