import { usePaysAdminStore } from '../stores/usePaysAdminStore'
import type { PaysCreate, PaysUpdate } from '../../types/pays'

export const usePaysAdmin = () => {
  const store = usePaysAdminStore()

  const allPays = computed(() => store.pays)
  const isFetching = computed(() => store.loading)

  const create = async (data: PaysCreate) => {
    await store.createPays(data)
  }

  const update = async (id: string, data: PaysUpdate) => {
    await store.updatePays(id, data)
  }

  const remove = async (id: string) => {
    await store.deletePays(id)
  }

  const refresh = () => store.fetchAllPays()

  return {
    allPays,
    isFetching,
    create,
    update,
    remove,
    refresh,
  }
}
