// composables/useProfileFormLogic.ts
import type { MinistereReadWithRelations } from '~~/layers/base/types/ministere'
import type { ProfilCreateFull, ProfilReadFull } from '~~/layers/base/types/profiles'

export function useProfileFormLogic() {
  // Mapping pour l'édition (Preremplissage)
  const mapProfileToForm = (p: ProfilReadFull): ProfilCreateFull => {
    const mIds = new Set(p.ministeres?.map((m) => m.id) || [])
    const pIds = p.poles?.map((pole) => pole.id) || []

    p.poles?.forEach((pole) => {
      if (pole.ministere_id) mIds.add(pole.ministere_id)
    })

    return {
      nom: p.nom,
      prenom: p.prenom,
      email: p.email,
      telephone: p.telephone ?? '',
      actif: p.actif,
      campus_ids: p.campuses?.map((c) => c.id) || [],
      campus_principal_id: p.campus_principal_id ?? null,
      ministere_ids: Array.from(mIds),
      pole_ids: pIds,
      role_codes: p.roles_assoc?.map((r) => r.role_code) || [],
      utilisateur: p.utilisateur
        ? { username: p.utilisateur.username, actif: p.utilisateur.actif, roles_ids: [] }
        : undefined,
    }
  }

  const toggleMinistere = (
    min: MinistereReadWithRelations,
    currentMIds: string[],
    currentPIds: string[],
  ) => {
    const mSet = new Set(currentMIds)
    const pSet = new Set(currentPIds)
    const childIds = min.poles.map((p) => p.id)

    if (mSet.has(min.id)) {
      mSet.delete(min.id)
      childIds.forEach((id) => pSet.delete(id))
    } else {
      mSet.add(min.id)
      childIds.forEach((id) => pSet.add(id))
    }
    return { ministere_ids: Array.from(mSet), pole_ids: Array.from(pSet) }
  }

  const togglePole = (
    ministereId: string,
    poleId: string,
    allMinisteres: MinistereReadWithRelations[],
    currentMIds: string[],
    currentPIds: string[],
  ) => {
    const pSet = new Set(currentPIds)
    const mSet = new Set(currentMIds)
    if (pSet.has(poleId)) {
      pSet.delete(poleId)
    } else {
      pSet.add(poleId)
    }

    const min = allMinisteres.find((m) => m.id === ministereId)
    if (min) {
      const hasAnyPole = min.poles.some((p) => pSet.has(p.id))
      if (hasAnyPole) {
        mSet.add(ministereId)
      } else {
        mSet.delete(ministereId)
      }
    }
    return { ministere_ids: Array.from(mSet), pole_ids: Array.from(pSet) }
  }

  return { mapProfileToForm, toggleMinistere, togglePole }
}
