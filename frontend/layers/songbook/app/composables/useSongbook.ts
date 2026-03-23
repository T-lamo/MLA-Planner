import { ref, computed } from 'vue'
import type {
  ChantCategorieCreate,
  ChantCategorieRead,
  ChantCategorieUpdate,
  ChantContenuCreate,
  ChantContenuUpdate,
  ChantCreate,
  ChantRead,
  ChantReadFull,
  ChantTransposeResponse,
  ChantUpdate,
  PaginatedChants,
} from '../types/chant'
import { ChantRepository } from '../repositories/ChantRepository'

// -----------------------------------------------------------------------
// Module-level singletons
// -----------------------------------------------------------------------

const categories = ref<ChantCategorieRead[]>([])
const chants = ref<ChantRead[]>([])
const total = ref(0)
const selectedChant = ref<ChantReadFull | null>(null)
const isLoading = ref(false)

const repo = new ChantRepository()

// -----------------------------------------------------------------------
// Composable exporté
// -----------------------------------------------------------------------

export const useSongbook = () => {
  const notify = useMLANotify()

  // -----------------------------------------------------------------------
  // Computed
  // -----------------------------------------------------------------------

  const categoriesOptions = computed(() =>
    categories.value.map((c) => ({ label: c.libelle, value: c.code })),
  )

  const categoriesByOrdre = computed(() => [...categories.value].sort((a, b) => a.ordre - b.ordre))

  // -----------------------------------------------------------------------
  // Chargement
  // -----------------------------------------------------------------------

  async function loadCategories(): Promise<void> {
    try {
      categories.value = await repo.listCategories()
    } catch {
      // Non bloquant
    }
  }

  async function loadChants(
    campusId?: string,
    opts: { q?: string; categorie?: string } = {},
  ): Promise<void> {
    isLoading.value = true
    try {
      const result: PaginatedChants = await repo.listChants({
        campus_id: campusId || undefined,
        q: opts.q,
        categorie_code: opts.categorie,
        limit: 100,
        offset: 0,
      })
      chants.value = result.data
      total.value = result.total
    } catch {
      // Erreur déjà notifiée par l'intercepteur
    } finally {
      isLoading.value = false
    }
  }

  async function selectChant(id: string): Promise<void> {
    try {
      selectedChant.value = await repo.getChant(id)
    } catch {
      // Non bloquant
    }
  }

  // -----------------------------------------------------------------------
  // Actions — Catégories
  // -----------------------------------------------------------------------

  async function createCategorie(payload: ChantCategorieCreate): Promise<void> {
    await repo.createCategorie(payload)
    notify.success('Catégorie créée')
    await loadCategories()
  }

  async function updateCategorie(code: string, payload: ChantCategorieUpdate): Promise<void> {
    await repo.updateCategorie(code, payload)
    notify.success('Catégorie mise à jour')
    await loadCategories()
  }

  async function deleteCategorie(code: string): Promise<void> {
    await repo.deleteCategorie(code)
    notify.success('Catégorie supprimée')
    await loadCategories()
  }

  // -----------------------------------------------------------------------
  // Actions — Chants
  // -----------------------------------------------------------------------

  async function createChant(payload: ChantCreate): Promise<ChantRead> {
    const created = await repo.createChant(payload)
    notify.success('Chant créé')
    return created
  }

  async function updateChant(id: string, payload: ChantUpdate): Promise<void> {
    const updated = await repo.updateChant(id, payload)
    if (selectedChant.value?.id === id) {
      selectedChant.value = { ...selectedChant.value, ...updated }
    }
    notify.success('Chant mis à jour')
  }

  async function deleteChant(id: string, campusId: string): Promise<void> {
    await repo.deleteChant(id)
    if (selectedChant.value?.id === id) {
      selectedChant.value = null
    }
    notify.success('Chant supprimé')
    await loadChants(campusId)
  }

  // -----------------------------------------------------------------------
  // Actions — Contenu
  // -----------------------------------------------------------------------

  async function upsertContenu(chantId: string, payload: ChantContenuCreate): Promise<void> {
    const contenu = await repo.upsertContenu(chantId, payload)
    if (selectedChant.value?.id === chantId) {
      selectedChant.value = { ...selectedChant.value, contenu }
    }
    notify.success('Contenu sauvegardé')
  }

  async function updateContenu(chantId: string, payload: ChantContenuUpdate): Promise<void> {
    const contenu = await repo.updateContenu(chantId, payload)
    if (selectedChant.value?.id === chantId) {
      selectedChant.value = { ...selectedChant.value, contenu }
    }
    notify.success('Contenu mis à jour')
  }

  async function transpose(
    chantId: string,
    semitones: number,
  ): Promise<ChantTransposeResponse | null> {
    try {
      return await repo.transpose(chantId, { semitones })
    } catch {
      return null
    }
  }

  return {
    // état
    categories,
    categoriesOptions,
    categoriesByOrdre,
    chants,
    total,
    selectedChant,
    isLoading,
    // chargement
    loadCategories,
    loadChants,
    selectChant,
    // catégories
    createCategorie,
    updateCategorie,
    deleteCategorie,
    // chants
    createChant,
    updateChant,
    deleteChant,
    // contenu
    upsertContenu,
    updateContenu,
    transpose,
  }
}
