<template>
  <section class="space-y-4">
    <div class="form-input-wrapper mb-4">
      <span class="form-input-icon"><Search class="size-3.5" /></span>
      <input
        v-model="search"
        type="text"
        class="form-input has-leading-icon"
        placeholder="Filtrer..."
      />
    </div>

    <div class="space-y-3">
      <div
        v-for="min in filtered"
        :key="min.id"
        class="ministere-accordion"
        :class="{ 'is-active': getState(min).isSelected }"
      >
        <!-- En-tête ministère -->
        <div
          class="flex cursor-pointer items-center justify-between p-3"
          @click="handleToggleAccordion(min)"
        >
          <div class="flex items-center gap-3">
            <div
              :class="[
                'flex size-5 shrink-0 items-center justify-center rounded-md border transition-all',
                getState(min).isSelected
                  ? 'bg-primary-600 border-primary-600'
                  : 'border-slate-200 bg-white',
              ]"
              @click.stop="$emit('toggleMinistere', min)"
            >
              <Check v-if="getState(min).isAllSelected" class="size-3.5 text-white" />
              <Minus v-else-if="getState(min).isIndeterminate" class="size-3.5 text-white" />
            </div>
            <div>
              <h4 class="mb-1 text-sm leading-none font-bold text-slate-700">{{ min.nom }}</h4>
              <span
                class="text-[10px] font-bold"
                :class="getState(min).selectedCount > 0 ? 'text-primary-600' : 'text-slate-400'"
              >
                {{ getState(min).selectedCount }} / {{ getState(min).totalPoles }} pôles
                <template v-if="roleCountForMinistere(min.id) > 0">
                  · {{ roleCountForMinistere(min.id) }} rôle(s)
                </template>
              </span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="text-primary-600 bg-primary-50 rounded px-2 py-1 text-[10px] font-black uppercase"
              @click.stop="$emit('toggleMinistere', min)"
            >
              {{ getState(min).isAllSelected ? 'Vider' : 'Tout cocher' }}
            </button>
            <ChevronDown
              :class="[
                'size-4 text-slate-400 transition-transform duration-300',
                openMinisteres.has(min.id) ? 'rotate-180' : '',
              ]"
            />
          </div>
        </div>

        <!-- Corps accordéon : pôles + rôles -->
        <Transition name="form-expand">
          <div
            v-show="openMinisteres.has(min.id) || search"
            class="border-t border-slate-100 bg-slate-50/50"
          >
            <!-- Pôles -->
            <div v-if="min.poles.length > 0" class="p-3">
              <p class="mb-2 text-[10px] font-bold tracking-wide text-slate-400 uppercase">Pôles</p>
              <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
                <button
                  v-for="pole in min.poles"
                  :key="pole.id"
                  type="button"
                  :class="['pole-pill', poleIds.includes(pole.id) ? 'active' : '']"
                  @click="$emit('togglePole', min.id, pole.id)"
                >
                  <span class="truncate">{{ pole.nom }}</span>
                </button>
              </div>
            </div>

            <!-- Séparateur + Rôles & Compétences -->
            <div class="border-t border-slate-100 p-3">
              <p class="mb-2 text-[10px] font-bold tracking-wide text-slate-400 uppercase">
                Rôles & Compétences
              </p>

              <!-- Skeleton -->
              <div v-if="loadingByMinistere[min.id]" class="space-y-2">
                <div v-for="n in 2" :key="n" class="h-10 animate-pulse rounded-lg bg-slate-200" />
              </div>

              <!-- Catalogue vide -->
              <p
                v-else-if="(categoriesByMinistere[min.id] ?? []).length === 0"
                class="text-xs text-slate-400 italic"
              >
                Aucun rôle configuré pour ce ministère.
              </p>

              <!-- Catégories de rôles -->
              <div v-else class="space-y-2">
                <div
                  v-for="cat in categoriesByMinistere[min.id] ?? []"
                  :key="cat.categorie_code"
                  class="cat-accordion"
                  :class="{ 'is-active': getCatState(cat).selectedCount > 0 }"
                >
                  <!-- En-tête catégorie -->
                  <div
                    class="flex cursor-pointer items-center justify-between px-3 py-2"
                    @click="toggleCatAccordion(min.id, cat.categorie_code)"
                  >
                    <div class="flex items-center gap-2">
                      <div
                        :class="[
                          'flex size-4 shrink-0 items-center justify-center rounded border transition-all',
                          getCatState(cat).selectedCount > 0
                            ? 'bg-primary-600 border-primary-600'
                            : 'border-slate-200 bg-white',
                        ]"
                        @click.stop="toggleCategoryRoles(cat)"
                      >
                        <Check v-if="getCatState(cat).isAllSelected" class="size-2.5 text-white" />
                        <Minus
                          v-else-if="getCatState(cat).isIndeterminate"
                          class="size-2.5 text-white"
                        />
                      </div>
                      <span class="text-xs font-semibold text-slate-700">
                        {{ cat.categorie_libelle }}
                      </span>
                      <span class="text-[10px] text-slate-400">
                        {{ getCatState(cat).selectedCount }}/{{ cat.roles.length }}
                      </span>
                    </div>
                    <div class="flex items-center gap-2">
                      <button
                        type="button"
                        class="text-primary-600 bg-primary-50 rounded px-1.5 py-0.5 text-[10px] font-black uppercase"
                        @click.stop="toggleCategoryRoles(cat)"
                      >
                        {{ getCatState(cat).isAllSelected ? 'Vider' : 'Tout' }}
                      </button>
                      <ChevronDown
                        :class="[
                          'size-3.5 text-slate-400 transition-transform duration-200',
                          openCatAccordions.has(`${min.id}:${cat.categorie_code}`)
                            ? 'rotate-180'
                            : '',
                        ]"
                      />
                    </div>
                  </div>

                  <!-- Pills rôles -->
                  <Transition name="form-expand">
                    <div
                      v-show="openCatAccordions.has(`${min.id}:${cat.categorie_code}`)"
                      class="border-t border-slate-100 bg-white px-3 py-2"
                    >
                      <div class="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
                        <button
                          v-for="role in cat.roles"
                          :key="role.code"
                          type="button"
                          :class="['role-pill', roleCodes.includes(role.code) ? 'active' : '']"
                          @click="toggleRole(role.code)"
                        >
                          <span class="truncate">{{ role.libelle }}</span>
                        </button>
                      </div>
                    </div>
                  </Transition>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { Search, Check, Minus, ChevronDown } from 'lucide-vue-next'
import type { MinistereReadWithRelations } from '~~/layers/base/types/ministere'
import type { RolesByCategoryItem } from '~~/layers/base/types/role-competence'
import { useRoleCompetenceStore } from '../../stores/useRoleCompetenceStore'

const props = defineProps<{
  ministeres: MinistereReadWithRelations[]
  ministereIds: string[]
  poleIds: string[]
  roleCodes: string[]
}>()

const emit = defineEmits<{
  toggleMinistere: [min: MinistereReadWithRelations]
  togglePole: [ministereId: string, poleId: string]
  'update:roleCodes': [value: string[]]
}>()

const roleStore = useRoleCompetenceStore()
const { categoriesByMinistere, loadingByMinistere } = storeToRefs(roleStore)

const search = ref('')
const openMinisteres = ref(new Set<string>())
const openCatAccordions = ref(new Set<string>())

const filtered = computed(() => {
  if (!search.value) return props.ministeres
  const s = search.value.toLowerCase()
  return props.ministeres.filter(
    (m) => m.nom.toLowerCase().includes(s) || m.poles.some((p) => p.nom.toLowerCase().includes(s)),
  )
})

const getState = (min: MinistereReadWithRelations) => {
  const isSelected = props.ministereIds.includes(min.id)
  const childIds = min.poles.map((p) => p.id)
  const selectedCount = childIds.filter((id) => props.poleIds.includes(id)).length
  return {
    isSelected,
    isIndeterminate: isSelected && selectedCount > 0 && selectedCount < childIds.length,
    isAllSelected: childIds.length > 0 && selectedCount === childIds.length,
    selectedCount,
    totalPoles: childIds.length,
  }
}

function roleCountForMinistere(ministereId: string): number {
  const cats = categoriesByMinistere.value[ministereId] ?? []
  const codes = cats.flatMap((c) => c.roles.map((r) => r.code))
  return codes.filter((c) => props.roleCodes.includes(c)).length
}

const getCatState = (cat: RolesByCategoryItem) => {
  const codes = cat.roles.map((r) => r.code)
  const selectedCount = codes.filter((c) => props.roleCodes.includes(c)).length
  return {
    selectedCount,
    isIndeterminate: selectedCount > 0 && selectedCount < codes.length,
    isAllSelected: codes.length > 0 && selectedCount === codes.length,
  }
}

function toggleRole(code: string): void {
  const next = props.roleCodes.includes(code)
    ? props.roleCodes.filter((c) => c !== code)
    : [...props.roleCodes, code]
  emit('update:roleCodes', next)
}

function toggleCategoryRoles(cat: RolesByCategoryItem): void {
  const codes = cat.roles.map((r) => r.code)
  const state = getCatState(cat)
  const next = state.isAllSelected
    ? props.roleCodes.filter((c) => !codes.includes(c))
    : [...new Set([...props.roleCodes, ...codes])]
  emit('update:roleCodes', next)
}

async function handleToggleAccordion(min: MinistereReadWithRelations): Promise<void> {
  if (openMinisteres.value.has(min.id)) {
    openMinisteres.value.delete(min.id)
  } else {
    openMinisteres.value.add(min.id)
    await roleStore.fetchByCategoryForMinistere(min.id)
  }
}

function toggleCatAccordion(ministereId: string, catCode: string): void {
  const key = `${ministereId}:${catCode}`
  if (openCatAccordions.value.has(key)) {
    openCatAccordions.value.delete(key)
  } else {
    openCatAccordions.value.add(key)
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.ministere-accordion {
  @apply overflow-hidden rounded-xl border border-slate-200 bg-white transition-all duration-200;
}
.ministere-accordion.is-active {
  border-color: color-mix(in srgb, var(--color-primary-600) 40%, white);
}
.cat-accordion {
  @apply overflow-hidden rounded-lg border border-slate-200 bg-slate-50 transition-all duration-150;
}
.cat-accordion.is-active {
  border-color: color-mix(in srgb, var(--color-primary-600) 30%, white);
}
.pole-pill {
  @apply flex items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-bold text-slate-600 transition-all active:scale-95;
}
.pole-pill.active {
  border-color: color-mix(in srgb, var(--color-primary-600) 30%, transparent);
  background-color: color-mix(in srgb, var(--color-primary-600) 10%, white);
  color: var(--color-primary-700);
}
.role-pill {
  @apply flex items-center justify-center rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-[11px] font-bold text-slate-600 transition-all active:scale-95;
}
.role-pill.active {
  border-color: color-mix(in srgb, var(--color-primary-600) 30%, transparent);
  background-color: color-mix(in srgb, var(--color-primary-600) 10%, white);
  color: var(--color-primary-700);
}
.form-expand-enter-active,
.form-expand-leave-active {
  transition: all 0.3s ease;
  max-height: 1200px;
  overflow: hidden;
}
.form-expand-enter-from,
.form-expand-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
