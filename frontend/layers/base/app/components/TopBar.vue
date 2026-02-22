<template>
  <header
    class="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-8"
  >
    <div class="flex items-center gap-2 md:gap-6">
      <button
        class="flex rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden"
        @click="ui.toggleSidebar"
      >
        <Menu class="size-6" />
      </button>

      <div ref="dropdownRef" class="relative min-w-[140px] md:min-w-[200px]">
        <button
          class="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 py-2 pr-2 pl-3 text-xs font-semibold text-slate-900 transition-all focus:ring-2 focus:ring-(--color-accent) md:text-sm"
          @click="isDropdownOpen = !isDropdownOpen"
        >
          <span class="truncate">{{ ui.selectedCampus }}</span>
          <ChevronDown
            :class="[
              'size-4 text-slate-500 transition-transform',
              isDropdownOpen ? 'rotate-180' : '',
            ]"
          />
        </button>

        <Transition name="scale-fade">
          <div
            v-if="isDropdownOpen"
            class="absolute top-full left-0 z-50 mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white p-1 shadow-xl shadow-slate-200/50"
          >
            <button
              v-for="campus in ui.campuses"
              :key="campus"
              :class="[
                'flex w-full items-center rounded-lg px-3 py-2 text-left text-xs transition-colors md:text-sm',
                ui.selectedCampus === campus
                  ? 'bg-(--color-primary-600)/10 font-bold text-(--color-primary-700)'
                  : 'text-slate-600 hover:bg-slate-50',
              ]"
              @click="selectCampus(campus)"
            >
              {{ campus }}
            </button>
          </div>
        </Transition>
      </div>

      <nav class="hidden items-center text-sm text-slate-500 lg:flex">
        <span>Planning</span>
        <ChevronRight class="mx-2 size-4" />
        <span class="font-semibold text-slate-900 capitalize">{{ currentRouteName }}</span>
      </nav>
    </div>

    <div class="flex items-center gap-2 md:gap-4">
      <button class="btn-primary flex items-center justify-center gap-2 px-3 py-2 md:px-4">
        <Plus class="size-5 md:size-4" />
        <span class="hidden md:inline">Créer Planning</span>
      </button>
      <button class="relative rounded-full p-2 text-slate-500 hover:bg-slate-50">
        <Bell class="size-5" />
        <span
          class="absolute top-1.5 right-1.5 size-2 rounded-full border-2 border-white bg-red-500"
        ></span>
      </button>
    </div>

    <div v-if="isDropdownOpen" class="fixed inset-0 z-40" @click="isDropdownOpen = false" />
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronDown, ChevronRight, Plus, Menu, Bell } from 'lucide-vue-next'
import { useUIStore } from '../stores/useUiStore'

const ui = useUIStore()
const route = useRoute()
const isDropdownOpen = ref(false)

const currentRouteName = computed(() => route.path.split('/').pop() || 'Dashboard')

const selectCampus = (campus: string) => {
  ui.selectedCampus = campus
  isDropdownOpen.value = false
}
</script>

<style scoped>
@reference "../assets/css/main.css";

.btn-primary {
  @apply rounded-lg bg-(--color-primary-600) font-semibold text-white transition-all hover:bg-(--color-primary-700) active:scale-95;
}

/* Animation fluide pour le dropdown */
.scale-fade-enter-active,
.scale-fade-leave-active {
  transition: all 0.15s ease-out;
}
.scale-fade-enter-from,
.scale-fade-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}
</style>
