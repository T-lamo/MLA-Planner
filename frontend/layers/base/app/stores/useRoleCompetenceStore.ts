import { defineStore } from 'pinia'
import { RoleCompetenceRepository } from '../repositories/RoleCompetenceRepository'
import type { RoleCompetenceRead, RolesByCategoryItem } from '../../types/role-competence'

export const useRoleCompetenceStore = defineStore('roleCompetence', () => {
  const repository = new RoleCompetenceRepository()

  // --- State ---
  const categories = ref<RolesByCategoryItem[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)

  // --- Getters ---
  const flatRoles = computed<RoleCompetenceRead[]>(() =>
    categories.value.flatMap((cat) => cat.roles),
  )

  // --- Actions ---
  async function fetchByCategory() {
    if (categories.value.length > 0) return
    loading.value = true
    error.value = null
    try {
      categories.value = await repository.getByCategory()
    } catch (e: unknown) {
      error.value = e
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    categories,
    loading,
    error,
    flatRoles,
    fetchByCategory,
  }
})
