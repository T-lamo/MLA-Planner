<template>
  <section class="space-y-4">
    <!-- <header class="section-header sticky top-0 z-10 bg-white py-2">
      <Building2 class="size-3.5" /><span>Ministères & Pôles</span>
    </header> -->
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
        <div
          class="flex cursor-pointer items-center justify-between p-3"
          @click="toggleAccordion(min.id)"
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

        <Transition name="form-expand">
          <div
            v-show="openMinisteres.has(min.id) || search"
            class="border-t border-slate-100 bg-slate-50/50 p-3"
          >
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
        </Transition>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, Check, Minus, ChevronDown } from 'lucide-vue-next'
import type { MinistereReadWithRelations } from '~~/layers/base/types/ministere'

const props = defineProps<{
  ministeres: MinistereReadWithRelations[]
  ministereIds: string[]
  poleIds: string[]
}>()

defineEmits(['toggleMinistere', 'togglePole'])

const search = ref('')
const openMinisteres = ref(new Set<string>())

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
const toggleAccordion = (id: string) =>
  openMinisteres.value.has(id) ? openMinisteres.value.delete(id) : openMinisteres.value.add(id)
</script>
<style scoped>
@reference "../../assets/css/main.css";

.ministere-accordion {
  @apply overflow-hidden rounded-xl border border-slate-200 bg-white transition-all duration-200;
}
.ministere-accordion.is-active {
  border-color: color-mix(in srgb, var(--color-primary-600) 40%, white);
}
.checkbox-box {
  @apply flex size-5 shrink-0 items-center justify-center rounded-md border border-slate-200 bg-white transition-all;
}
.checkbox-box.active {
  @apply bg-primary-600 border-primary-600;
}
.btn-batch {
  @apply text-primary-600 bg-primary-50 rounded px-2 py-1 text-[10px] font-black uppercase;
}
.accordion-content {
  @apply border-t border-slate-100 bg-slate-50/50 p-3;
}
.pole-pill {
  @apply flex items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-bold text-slate-600 transition-all active:scale-95;
}
.pole-pill.active {
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
