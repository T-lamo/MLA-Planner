<script setup lang="ts">
import { ref } from 'vue'
import { ChevronDown, Check } from 'lucide-vue-next'
import { onClickOutside } from '@vueuse/core'
import { useUIStore } from '../stores/useUiStore'

const ui = useUIStore()
const isDropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

// Gestion clic extérieur avec VueUse
onClickOutside(dropdownRef, () => (isDropdownOpen.value = false))

const selectCampus = (id: string) => {
  ui.selectedCampusId = id
  isDropdownOpen.value = false
}
</script>

<template>
  <div ref="dropdownRef" class="relative min-w-[160px] md:min-w-[220px]">
    <button
      type="button"
      class="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 py-2 pr-2 pl-3 text-xs font-semibold text-slate-900 transition-all hover:border-slate-300 focus:ring-2 focus:ring-(--color-primary-600) focus:outline-hidden md:text-sm"
      aria-haspopup="listbox"
      :aria-expanded="isDropdownOpen"
      @click="isDropdownOpen = !isDropdownOpen"
    >
      <span class="truncate">
        {{ ui.currentCampus?.nom || 'Sélectionner un campus' }}
      </span>
      <ChevronDown
        :class="[
          'ml-2 size-4 text-slate-500 transition-transform duration-200',
          isDropdownOpen ? 'rotate-180' : '',
        ]"
      />
    </button>

    <Transition name="scale-fade">
      <div
        v-if="isDropdownOpen"
        class="absolute top-full left-0 z-50 mt-1.5 w-full overflow-hidden rounded-xl border border-slate-200 bg-white p-1 shadow-xl shadow-slate-200/50"
        role="listbox"
      >
        <div v-if="ui.myCampuses.length === 0" class="px-3 py-4 text-center text-xs text-slate-400">
          Aucun campus assigné
        </div>

        <button
          v-for="campus in ui.myCampuses"
          :key="campus.id"
          role="option"
          :aria-selected="ui.selectedCampusId === campus.id"
          :class="[
            'flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-xs transition-colors md:text-sm',
            ui.selectedCampusId === campus.id
              ? 'bg-(--color-primary-600)/10 font-bold text-(--color-primary-700)'
              : 'text-slate-600 hover:bg-slate-50',
          ]"
          @click="selectCampus(campus.id)"
        >
          <span class="truncate">{{ campus.nom }}</span>
          <Check v-if="ui.selectedCampusId === campus.id" class="size-4 shrink-0" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
@reference "../assets/css/main.css";

.scale-fade-enter-active,
.scale-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.scale-fade-enter-from,
.scale-fade-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-8px);
}
</style>
