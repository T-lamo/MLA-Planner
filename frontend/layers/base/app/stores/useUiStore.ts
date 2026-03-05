import { defineStore } from 'pinia'
import { useCampusStore } from './useCampusStore'

export const useUIStore = defineStore('ui', () => {
  // --- Dependency Injection ---
  const campusStore = useCampusStore()

  // --- State ---
  const isSidebarCollapsed = ref(false)

  /**
   * PERSISTENCE STRATEGY:
   * To maintain the selection after a refresh in Nuxt 3,
   * we use useCookie (SSR friendly) or watch with localStorage.
   */
  const selectedCampusId = ref<string>('')

  // --- Computed (Reactive Synchronization) ---

  // Direct reference to the domain store's items
  const campuses = computed(() => campusStore.items)

  // Dynamically find the full object from the domain store
  const currentCampus = computed(() => {
    if (!selectedCampusId.value) return null
    return campusStore.getById(selectedCampusId.value)
  })

  // --- Actions ---

  const toggleSidebar = () => (isSidebarCollapsed.value = !isSidebarCollapsed.value)

  /**
   * Bootstrapping Logic:
   * Ensures data is present and handles default selection.
   */
  async function initializeUI() {
    // 1. Fetch campuses if the domain store is empty
    if (campusStore.items.length === 0) {
      // We fetch with a large limit to ensure we have the referential list for the UI
      await campusStore.fetchAll({ limit: 100, offset: 0 })
    }

    // 2. Default Selection Logic
    // If no ID is selected or the selected ID no longer exists in the list
    const exists = campusStore.items.some((c) => c.id === selectedCampusId.value)

    // 1. Vérification de l'existence et de l'expiration
    if (!selectedCampusId.value || !exists) {
      if (campusStore.items && campusStore.items.length > 0) {
        const firstCampus = campusStore.items[0]

        if (firstCampus) {
          selectedCampusId.value = firstCampus.id
        }
      }
    }
  }

  /**
   * Persistence Recommendation:
   * Uncomment the following to persist selection in local storage
   */
  /*
  watch(selectedCampusId, (newId) => {
    if (newId) localStorage.setItem('selected_campus_id', newId)
  }, { immediate: true })
  
  // In the setup part of the store:
  // selectedCampusId.value = localStorage.getItem('selected_campus_id') || null
  */

  return {
    isSidebarCollapsed,
    selectedCampusId,
    campuses,
    currentCampus,
    toggleSidebar,
    initializeUI,
  }
})
