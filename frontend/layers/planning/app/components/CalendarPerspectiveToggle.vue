<template>
  <div class="inline-flex items-center gap-1 rounded-xl bg-slate-100 p-1">
    <button
      v-for="opt in options"
      :key="opt.value"
      :class="[
        'rounded-lg px-4 py-2 text-xs font-bold transition-all',
        modelValue === opt.value
          ? 'bg-white text-(--color-primary-700) shadow-sm'
          : 'text-slate-500 hover:text-slate-700',
      ]"
      @click="$emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { PlanningViewPerspective } from '../types/planning.types'

defineProps<{ modelValue: PlanningViewPerspective }>()
defineEmits(['update:modelValue'])

const options: { label: string; value: PlanningViewPerspective }[] = [
  { label: 'Mon Planning', value: 'PERSONAL' },
  { label: 'Mon Ministère', value: 'MINISTERE' },
  { label: 'Tout le Campus', value: 'CAMPUS' },
]
</script>
