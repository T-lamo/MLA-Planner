// layers/base/app/stores/useUIStore.ts
import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', () => {
  const isSidebarCollapsed = ref(false)
  const selectedCampus = ref('Paris - Cité Royale')
  const campuses = ['Paris - Cité Royale', 'Brazzaville', 'Montréal', 'Abidjan']

  const toggleSidebar = () => (isSidebarCollapsed.value = !isSidebarCollapsed.value)

  return { isSidebarCollapsed, selectedCampus, campuses, toggleSidebar }
})
