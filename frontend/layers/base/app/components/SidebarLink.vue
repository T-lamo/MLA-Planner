<template>
  <li>
    <NuxtLink
      :to="to"
      class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
      activeClass="bg-(--color-primary-600)/10 text-(--color-primary-700)!"
    >
      <component :is="icon" class="size-5 shrink-0" />
      <span v-if="!collapsed" class="truncate">{{ label }}</span>

      <span
        v-if="!collapsed && badge"
        class="ml-auto rounded-full bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-600"
      >
        {{ badge }}
      </span>
    </NuxtLink>
  </li>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
defineProps<{
  to: string
  icon: Component
  label: string
  collapsed: boolean
  badge?: number
}>()
</script>
