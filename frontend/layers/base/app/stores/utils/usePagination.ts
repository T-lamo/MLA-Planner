import { reactive } from 'vue'

export function usePagination(defaultLimit = 10) {
  const pagination = reactive({
    limit: defaultLimit,
    offset: 0,
  })

  function setPagination(offset: number, limit?: number) {
    pagination.offset = offset
    if (limit) pagination.limit = limit
  }

  function resetPagination() {
    pagination.offset = 0
    pagination.limit = defaultLimit
  }

  return {
    pagination,
    setPagination,
    resetPagination,
  }
}
