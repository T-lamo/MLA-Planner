import { ref } from 'vue'

// Compteur global : chaque AppDrawer ouvert incrémente et récupère sa profondeur
const openCount = ref(0)

export function useDrawerStack() {
  function acquire(): number {
    openCount.value++
    return openCount.value
  }

  function release(): void {
    if (openCount.value > 0) {
      openCount.value--
    }
  }

  return { acquire, release }
}
