<template>
  <div class="inline-flex items-center gap-1 rounded-xl bg-slate-100 p-1">
    <button
      v-for="opt in options"
      :key="opt.value"
      :class="[
        'flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold transition-all',
        modelValue === opt.value
          ? 'bg-white text-(--color-primary-700) shadow-sm'
          : 'text-slate-500 hover:text-slate-700',
      ]"
      @click="$emit('update:modelValue', opt.value)"
    >
      <component :is="opt.icon" class="size-3.5 shrink-0" />
      <span class="hidden sm:inline">{{ opt.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import { User, Building2, Globe2 } from 'lucide-vue-next'
import type { PlanningViewPerspective } from '../types/planning.types'

defineProps<{ modelValue: PlanningViewPerspective }>()
defineEmits(['update:modelValue'])

const options: { label: string; value: PlanningViewPerspective; icon: Component }[] = [
  { label: 'Mon Planning', value: 'PERSONAL', icon: User },
  { label: 'Mon Ministère', value: 'MINISTERE', icon: Building2 },
  { label: 'Tout le Campus', value: 'CAMPUS', icon: Globe2 },
]
</script>
