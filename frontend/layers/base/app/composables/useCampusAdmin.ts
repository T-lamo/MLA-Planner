import { useCampusAdminStore } from '../stores/useCampusAdminStore'
import type { CampusCreate, CampusUpdate } from '../../types/campus'

export const useCampusAdmin = () => {
  const store = useCampusAdminStore()

  const allCampuses = computed(() => store.allCampuses)
  const isFetching = computed(() => store.loading)

  const create = async (data: CampusCreate) => {
    await store.createCampus(data)
  }

  const update = async (id: string, data: CampusUpdate) => {
    await store.updateCampus(id, data)
  }

  const remove = async (id: string) => {
    await store.deleteCampus(id)
  }

  const refresh = () => store.fetchAllCampuses()

  return {
    allCampuses,
    isFetching,
    create,
    update,
    remove,
    refresh,
  }
}
