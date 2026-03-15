import { ref } from 'vue'
import type {
  CampusSetupPayload,
  CampusSummaryMinistere,
  CategorieSetupItem,
  MinistereSetupItem,
  RoleSetupItem,
} from '~~/layers/base/types/campus-config'
import type { RoleCompetenceRead } from '~~/layers/base/types/role-competence'

// -----------------------------------------------------------------------
// Module-level singletons
// -----------------------------------------------------------------------

const isOpen = ref(false)
const isSubmitting = ref(false)

const _emptyRole = (): RoleSetupItem => ({ code: '', libelle: '' })
const _emptyCategorie = (): CategorieSetupItem => ({ nom: '', roles: [] })
const _emptyMinistere = (): MinistereSetupItem => ({
  nom: '',
  init_rbac: true,
  categories: [_emptyCategorie()],
})

const form = ref<CampusSetupPayload>({
  init_statuts: true,
  ministeres: [_emptyMinistere()],
})

// -----------------------------------------------------------------------
// Composable exporté
// -----------------------------------------------------------------------

export const useCampusSetup = () => {
  function open(
    existingMinisteres: CampusSummaryMinistere[] = [],
    allRoles: RoleCompetenceRead[] = [],
  ): void {
    if (existingMinisteres.length > 0) {
      form.value = {
        init_statuts: false,
        ministeres: existingMinisteres.map(
          (min): MinistereSetupItem => ({
            nom: min.nom,
            description: min.description,
            init_rbac: false,
            categories: min.categories.map(
              (cat): CategorieSetupItem => ({
                nom: cat.libelle,
                description: cat.description,
                roles: allRoles
                  .filter((r) => r.categorie_code === cat.code)
                  .map(
                    (r): RoleSetupItem => ({
                      code: r.code,
                      libelle: r.libelle,
                      description: r.description,
                    }),
                  ),
              }),
            ),
          }),
        ),
      }
    } else {
      form.value = { init_statuts: true, ministeres: [_emptyMinistere()] }
    }
    isOpen.value = true
  }

  function close(): void {
    isOpen.value = false
  }

  function addMinistere(): void {
    form.value.ministeres.push(_emptyMinistere())
  }

  function removeMinistere(mIdx: number): void {
    form.value.ministeres.splice(mIdx, 1)
  }

  function addCategorie(mIdx: number): void {
    form.value.ministeres[mIdx]!.categories.push(_emptyCategorie())
  }

  function removeCategorie(mIdx: number, cIdx: number): void {
    form.value.ministeres[mIdx]!.categories.splice(cIdx, 1)
  }

  function addRole(mIdx: number, cIdx: number): void {
    form.value.ministeres[mIdx]!.categories[cIdx]!.roles.push(_emptyRole())
  }

  function removeRole(mIdx: number, cIdx: number, rIdx: number): void {
    form.value.ministeres[mIdx]!.categories[cIdx]!.roles.splice(rIdx, 1)
  }

  return {
    isOpen,
    isSubmitting,
    form,
    open,
    close,
    addMinistere,
    removeMinistere,
    addCategorie,
    removeCategorie,
    addRole,
    removeRole,
  }
}
