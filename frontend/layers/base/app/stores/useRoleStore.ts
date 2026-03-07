import { defineStore } from 'pinia'
import { BaseRepository } from '../repositories/BaseRepository'

export interface RoleRead {
  id: string
  libelle: string
}

class RoleRepository extends BaseRepository {
  async getRoles(): Promise<RoleRead[]> {
    const { data } = await this.apiRequest<RoleRead[]>('/roles/')
    return data ?? []
  }
}

const repository = new RoleRepository()

export const useRoleStore = defineStore('roles', () => {
  const items = ref<RoleRead[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  let fetched = false

  async function fetchRoles() {
    if (fetched) return
    loading.value = true
    error.value = null
    try {
      items.value = await repository.getRoles()
      fetched = true
    } catch (e: unknown) {
      error.value = e
      throw e
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, fetchRoles }
})
