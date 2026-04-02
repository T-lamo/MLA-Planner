import { ref, computed } from 'vue'
import { PlanningRepository } from '../repositories/PlanningRepository'
import type { PlanningChantRead } from '../types/planning.types'

/**
 * Gestion du répertoire de chants d'un planning.
 *
 * Usage :
 *   const repertoire = useRepertoire()
 *   // charger depuis un planning existant :
 *   repertoire.loadFromPlanning(planning.chants)
 *   // sauvegarder :
 *   await repertoire.save(planningId)
 */
export function useRepertoire() {
  const repo = new PlanningRepository()

  // Liste locale (ordre éditable)
  const chants = ref<PlanningChantRead[]>([])
  const isSaving = ref(false)

  const isDirty = ref(false)

  // ── Initialisation depuis le planning déjà chargé ────────────────────────
  function loadFromPlanning(items: PlanningChantRead[]) {
    chants.value = [...items].sort((a, b) => a.ordre - b.ordre)
    isDirty.value = false
  }

  // ── Mutation locale ───────────────────────────────────────────────────────
  function addChant(chant: PlanningChantRead) {
    if (chants.value.some((c) => c.id === chant.id)) return
    chants.value.push({ ...chant, ordre: chants.value.length })
    isDirty.value = true
  }

  function removeChant(chantId: string) {
    chants.value = chants.value.filter((c) => c.id !== chantId).map((c, i) => ({ ...c, ordre: i }))
    isDirty.value = true
  }

  function moveUp(index: number) {
    if (index <= 0) return
    const arr = [...chants.value]
    ;[arr[index - 1], arr[index]] = [arr[index]!, arr[index - 1]!]
    chants.value = arr.map((c, i) => ({ ...c, ordre: i }))
    isDirty.value = true
  }

  function moveDown(index: number) {
    if (index >= chants.value.length - 1) return
    const arr = [...chants.value]
    ;[arr[index], arr[index + 1]] = [arr[index + 1]!, arr[index]!]
    chants.value = arr.map((c, i) => ({ ...c, ordre: i }))
    isDirty.value = true
  }

  // ── Persistance ───────────────────────────────────────────────────────────
  async function save(planningId: string): Promise<void> {
    if (!isDirty.value || isSaving.value) return
    isSaving.value = true
    try {
      const updated = await repo.setRepertoire(planningId, {
        chant_ids: chants.value.map((c) => c.id),
      })
      chants.value = updated
      isDirty.value = false
    } finally {
      isSaving.value = false
    }
  }

  const isEmpty = computed(() => chants.value.length === 0)

  return {
    chants,
    isDirty,
    isSaving,
    isEmpty,
    loadFromPlanning,
    addChant,
    removeChant,
    moveUp,
    moveDown,
    save,
  }
}

export type UseRepertoireReturn = ReturnType<typeof useRepertoire>
