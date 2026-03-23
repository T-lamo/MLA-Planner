import { useOrganisationStore } from '../stores/useOrganisationStore'
import type { OrganisationCreate, OrganisationUpdate } from '../../types/organisation'

export const useOrganisations = () => {
  const store = useOrganisationStore()

  const organisations = computed(() => store.organisations)
  const isFetching = computed(() => store.loading)

  const create = async (data: OrganisationCreate) => {
    await store.createOrganisation(data)
  }

  const update = async (id: string, data: OrganisationUpdate) => {
    await store.updateOrganisation(id, data)
  }

  const remove = async (id: string) => {
    await store.deleteOrganisation(id)
  }

  const refresh = () => store.fetchOrganisations()

  return {
    organisations,
    isFetching,
    create,
    update,
    remove,
    refresh,
  }
}
