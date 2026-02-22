<template>
  <div class="space-y-6">
    <div class="flex flex-col justify-between gap-4 md:flex-row md:items-center">
      <h1 class="text-2xl font-bold text-slate-800">Gestion des Services</h1>

      <div class="flex w-fit rounded-lg bg-slate-100 p-1">
        <NuxtLink
          to="/planning/calendar"
          class="flex items-center gap-2 rounded-md px-4 py-1.5 text-sm transition-all"
          activeClass="bg-white shadow-sm text-(--color-primary-700) font-bold"
        >
          <CalendarDays class="size-4" />
          <span>Calendrier</span>
        </NuxtLink>
        <NuxtLink
          to="/planning/list"
          class="flex items-center gap-2 rounded-md px-4 py-1.5 text-sm transition-all"
          activeClass="bg-white shadow-sm text-(--color-primary-700) font-bold"
        >
          <ListTodo class="size-4" />
          <span>Liste</span>
        </NuxtLink>
      </div>
    </div>

    <div class="relative">
      <NuxtPage />
    </div>
  </div>
</template>

<script setup lang="ts">
import { CalendarDays, ListTodo } from 'lucide-vue-next'
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition: all 0.2s ease-in-out;
}
.page-enter-from {
  opacity: 0;
  transform: translateX(10px);
}
.page-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>
