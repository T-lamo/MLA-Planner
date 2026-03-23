import { storeToRefs } from 'pinia'
import { useMinistereStore } from '../stores/useMinistereStore'

export const useMinisteres = () => {
  const store = useMinistereStore()

  // Utilisation de storeToRefs pour garder la réactivité des états
  const { items, currentMinistere, total, loading, error, pagination } = storeToRefs(store)

  /**
   * Wrapper pour fetchAll.
   * On peut passer des filtres additionnels qui fusionneront avec la pagination du store.
   */
  const loadMinisteres = async (params: Record<string, unknown> = {}) => {
    try {
      await store.fetchAll(params)
    } catch {
      // errors are handled by the global fetch interceptor
    }
  }

  /**
   * Charge le détail complet (relations incluses)
   */
  const loadFullMinistere = async (id: string) => {
    if (!id) return
    try {
      return await store.fetchFullById(id)
    } catch {
      // errors are handled by the global fetch interceptor
    }
  }

  /**
   * Met à jour la pagination et déclenche automatiquement un rechargement.
   * On utilise la méthode setPagination injectée dans le store par usePagination.
   */
  const changePage = async (offset: number, limit?: number) => {
    store.setPagination(offset, limit)
    await loadMinisteres()
  }

  /**
   * Lifecycle : Nettoyage automatique
   */
  onUnmounted(() => {
    store.resetCurrent()
    // Optionnel : store.resetPagination() si on veut repartir à zéro à chaque visite
  })

  return {
    // --- State (Refs) ---
    ministeres: items,
    ministereDetail: currentMinistere,
    totalCount: total,
    isLoading: loading,
    apiError: error,
    pagination, // Accès direct à reactive({limit, offset})

    // --- Business Methods ---
    loadMinisteres,
    loadFullMinistere,
    createMinistere: store.create,
    updateMinistere: store.update,
    deleteMinistere: store.remove,

    // --- Pagination Methods ---
    setPagination: changePage, // Version améliorée qui fetch auto
    resetPagination: async () => {
      store.resetPagination()
      await loadMinisteres()
    },
  }
}
