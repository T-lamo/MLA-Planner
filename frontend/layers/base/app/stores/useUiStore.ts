import { defineStore } from 'pinia'
import { useCampusStore } from './useCampusStore'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

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
      await campusStore.fetchAll({ limit: 100, offset: 0 })
    }

    // 2. Si l'utilisateur a déjà sélectionné un campus valide dans la session, on le conserve
    const currentIsValid = campusStore.items.some((c) => c.id === selectedCampusId.value)
    if (selectedCampusId.value && currentIsValid) return

    // 3. Priorité 1 : campus principal de l'utilisateur connecté
    const authStore = useAuthStore()
    const principalId = authStore.currentUser?.campusPrincipalId
    if (principalId && campusStore.items.some((c) => c.id === principalId)) {
      selectedCampusId.value = principalId
      return
    }

    // 4. Fallback : premier campus de la liste
    const firstCampus = campusStore.items[0]
    if (firstCampus) {
      selectedCampusId.value = firstCampus.id
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
