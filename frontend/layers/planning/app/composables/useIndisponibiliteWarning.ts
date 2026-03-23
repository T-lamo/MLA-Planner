// composables/useIndisponibiliteWarning.ts
import { ref } from 'vue'
import type { IndisponibiliteReadFull } from '~~/layers/base/types/indisponibilites'
import { IndisponibiliteRepository } from '~~/layers/base/app/repositories/IndisponibiliteRepository'

const repo = new IndisponibiliteRepository()

export function useIndisponibiliteWarning() {
  const unavailabilities = ref<IndisponibiliteReadFull[]>([])
  const loaded = ref(false)

  async function loadForPeriod(
    campusId: string,
    dateDebut: string,
    dateFin: string,
  ): Promise<void> {
    if (!campusId || !dateDebut || !dateFin) return
    try {
      unavailabilities.value = await repo.getValidatedForPeriod(campusId, dateDebut, dateFin)
    } catch {
      unavailabilities.value = []
    } finally {
      loaded.value = true
    }
  }

  function isMemberUnavailable(membreId: string): boolean {
    return unavailabilities.value.some((u) => u.membre_id === membreId)
  }

  function getWarningTooltip(membreId: string): string {
    const match = unavailabilities.value.find((u) => u.membre_id === membreId)
    if (!match) return ''
    const from = match.date_debut ?? ''
    const to = match.date_fin ?? ''
    const motif = match.motif ? ` — ${match.motif}` : ''
    return `Indisponible du ${from} au ${to}${motif}`
  }

  return {
    unavailabilities,
    loaded,
    loadForPeriod,
    isMemberUnavailable,
    getWarningTooltip,
  }
}
