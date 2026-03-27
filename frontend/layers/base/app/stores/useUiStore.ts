import { defineStore } from 'pinia'
import type { CampusRead } from '~~/layers/base/types/campus'

export const useUIStore = defineStore('ui', () => {
  // --- State ---
  const isSidebarCollapsed = ref(false)
  const myCampuses = ref<CampusRead[]>([])
  const selectedCampusId = ref<string>('')

  // --- Computed ---

  // myCampuses exposed as campuses for backward-compat (ProfileFilters, useProfiles)
  const campuses = computed(() => myCampuses.value)

  const currentCampus = computed(
    () => myCampuses.value.find((c) => c.id === selectedCampusId.value) ?? null,
  )

  // --- Actions ---

  const toggleSidebar = () => (isSidebarCollapsed.value = !isSidebarCollapsed.value)

  /**
   * Bootstrapping: always loads user's campuses first so the navbar
   * selector stays populated after SPA navigation, then selects a default.
   */
  async function initializeUI() {
    try {
      const { ProfileRepository } =
        await import('~~/layers/base/app/repositories/ProfileRepository')
      const profileRepo = new ProfileRepository()
      myCampuses.value = await profileRepo.getMyCampuses()
    } catch {
      // Silently ignore — ex: utilisateur non authentifié (page login)
      return
    }

    // Keep current selection if still valid
    const currentIsValid = myCampuses.value.some((c) => c.id === selectedCampusId.value)
    if (selectedCampusId.value && currentIsValid) return

    // Fallback: first campus in the list
    selectedCampusId.value = myCampuses.value[0]?.id ?? ''
  }

  return {
    isSidebarCollapsed,
    selectedCampusId,
    campuses,
    myCampuses,
    currentCampus,
    toggleSidebar,
    initializeUI,
  }
})
