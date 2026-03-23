<template>
  <section class="space-y-4">
    <div v-if="loading" class="space-y-2">
      <div v-for="n in 3" :key="n" class="h-12 animate-pulse rounded-xl bg-slate-100" />
    </div>

    <div v-else-if="categories.length === 0" class="py-4 text-center text-sm text-slate-400">
      Aucune compétence disponible.
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="cat in categories"
        :key="cat.categorie_code"
        class="category-accordion"
        :class="{ 'is-active': getCategoryState(cat).selectedCount > 0 }"
      >
        <div
          class="flex cursor-pointer items-center justify-between p-3"
          @click="toggleAccordion(cat.categorie_code)"
        >
          <div class="flex items-center gap-3">
            <div
              :class="[
                'flex size-5 shrink-0 items-center justify-center rounded-md border transition-all',
                getCategoryState(cat).selectedCount > 0
                  ? 'bg-primary-600 border-primary-600'
                  : 'border-slate-200 bg-white',
              ]"
              @click.stop="toggleCategory(cat)"
            >
              <Check v-if="getCategoryState(cat).isAllSelected" class="size-3.5 text-white" />
              <Minus
                v-else-if="getCategoryState(cat).isIndeterminate"
                class="size-3.5 text-white"
              />
            </div>
            <div>
              <h4 class="mb-1 text-sm leading-none font-bold text-slate-700">
                {{ cat.categorie_libelle }}
              </h4>
              <span
                class="text-[10px] font-bold"
                :class="
                  getCategoryState(cat).selectedCount > 0 ? 'text-primary-600' : 'text-slate-400'
                "
              >
                {{ getCategoryState(cat).selectedCount }} / {{ cat.roles.length }} compétences
              </span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="text-primary-600 bg-primary-50 rounded px-2 py-1 text-[10px] font-black uppercase"
              @click.stop="toggleCategory(cat)"
            >
              {{ getCategoryState(cat).isAllSelected ? 'Vider' : 'Tout cocher' }}
            </button>
            <ChevronDown
              :class="[
                'size-4 text-slate-400 transition-transform duration-300',
                openCategories.has(cat.categorie_code) ? 'rotate-180' : '',
              ]"
            />
          </div>
        </div>

        <Transition name="form-expand">
          <div
            v-show="openCategories.has(cat.categorie_code)"
            class="border-t border-slate-100 bg-slate-50/50 p-3"
          >
            <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <button
                v-for="role in cat.roles"
                :key="role.code"
                type="button"
                :class="['role-pill', modelValue.includes(role.code) ? 'active' : '']"
                @click="toggleRole(role.code)"
              >
                <span class="truncate">{{ role.libelle }}</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Check, Minus, ChevronDown } from 'lucide-vue-next'
import { useRoleCompetenceStore } from '../../stores/useRoleCompetenceStore'
import type { RolesByCategoryItem } from '~~/layers/base/types/role-competence'

const props = defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const roleStore = useRoleCompetenceStore()
const { categories, loading } = storeToRefs(roleStore)

onMounted(() => roleStore.fetchByCategory())

const openCategories = ref(new Set<string>())

const getCategoryState = (cat: RolesByCategoryItem) => {
  const roleCodes = cat.roles.map((r) => r.code)
  const selectedCount = roleCodes.filter((c) => props.modelValue.includes(c)).length
  return {
    selectedCount,
    isIndeterminate: selectedCount > 0 && selectedCount < roleCodes.length,
    isAllSelected: roleCodes.length > 0 && selectedCount === roleCodes.length,
  }
}

const toggleRole = (code: string) => {
  const next = props.modelValue.includes(code)
    ? props.modelValue.filter((c) => c !== code)
    : [...props.modelValue, code]
  emit('update:modelValue', next)
}

const toggleCategory = (cat: RolesByCategoryItem) => {
  const roleCodes = cat.roles.map((r) => r.code)
  const state = getCategoryState(cat)
  if (state.isAllSelected) {
    emit(
      'update:modelValue',
      props.modelValue.filter((c) => !roleCodes.includes(c)),
    )
  } else {
    const merged = [...new Set([...props.modelValue, ...roleCodes])]
    emit('update:modelValue', merged)
  }
}

const toggleAccordion = (code: string) => {
  if (openCategories.value.has(code)) {
    openCategories.value.delete(code)
  } else {
    openCategories.value.add(code)
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.category-accordion {
  @apply overflow-hidden rounded-xl border border-slate-200 bg-white transition-all duration-200;
}
.category-accordion.is-active {
  border-color: color-mix(in srgb, var(--color-primary-600) 40%, white);
}
.role-pill {
  @apply flex items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-bold text-slate-600 transition-all active:scale-95;
}
.role-pill.active {
  border-color: color-mix(in srgb, var(--color-primary-600) 30%, transparent);
  background-color: color-mix(in srgb, var(--color-primary-600) 10%, white);
  color: var(--color-primary-700);
}
.form-expand-enter-active,
.form-expand-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
}
.form-expand-enter-from,
.form-expand-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
