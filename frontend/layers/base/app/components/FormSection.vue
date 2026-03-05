<script setup lang="ts">
import type { Component } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

interface Props {
  title: string
  icon: Component
  isOpen: boolean
  badge?: string | number
}

defineProps<Props>()
const emit = defineEmits(['toggle'])
</script>

<template>
  <div class="form-section" :class="{ 'is-open': isOpen }">
    <button type="button" class="section-trigger" :aria-expanded="isOpen" @click="emit('toggle')">
      <div class="flex items-center gap-3">
        <div class="icon-container">
          <component :is="icon" class="size-4" />
        </div>
        <span class="section-title">{{ title }}</span>
        <span v-if="badge !== undefined && !isOpen" class="section-badge">
          {{ badge }}
        </span>
      </div>

      <div class="flex items-center gap-3">
        <slot name="actions" />
        <ChevronDown class="chevron-icon" :class="{ 'rotate-180': isOpen }" />
      </div>
    </button>

    <Transition name="section-slide">
      <div v-if="isOpen" class="section-content">
        <div class="px-1 pt-2 pb-4">
          <slot />
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
@reference "../assets/css/main.css";

.form-section {
  @apply border-b border-slate-100 transition-all duration-300;
}

.section-trigger {
  @apply flex w-full items-center justify-between py-4 text-left transition-all outline-none;
  @apply -mx-2 rounded-lg px-2 hover:bg-slate-50/50;
}

.icon-container {
  @apply flex size-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500 transition-colors;
}

.is-open .icon-container {
  @apply bg-primary-50 text-primary-600;
}

.section-title {
  @apply text-[11px] font-black tracking-widest text-slate-700 uppercase;
}

.section-badge {
  @apply flex h-5 items-center justify-center rounded-full bg-slate-100 px-2 text-[10px] font-bold text-slate-500;
}

.chevron-icon {
  @apply size-4 text-slate-400 transition-transform duration-300;
}

/* Slide Transition */
.section-slide-enter-active,
.section-slide-leave-active {
  @apply max-h-[1000px] overflow-hidden transition-all duration-300 ease-in-out;
}

.section-slide-enter-from,
.section-slide-leave-to {
  @apply max-h-0 opacity-0;
}
</style>
