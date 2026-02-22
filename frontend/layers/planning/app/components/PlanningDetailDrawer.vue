<template>
  <AppDrawer :isOpen="!!event" :title="event?.title" @close="$emit('close')">
    <div v-if="event" class="space-y-6">
      <div class="flex items-center gap-2">
        <span
          :class="[
            'rounded-full px-2.5 py-0.5 text-[10px] font-bold tracking-wider uppercase',
            event.extendedProps.statut === 'VALIDÉ'
              ? 'bg-emerald-100 text-emerald-600'
              : 'bg-amber-100 text-amber-600',
          ]"
        >
          {{ event.extendedProps.statut }}
        </span>
        <span class="text-xs text-slate-400">•</span>
        <span class="text-xs font-medium text-slate-500">{{
          event.extendedProps.typeActivite
        }}</span>
      </div>

      <div class="space-y-3 rounded-xl bg-slate-50 p-4">
        <div class="flex items-center gap-3 text-slate-600">
          <Calendar class="size-4 text-slate-400" />
          <span class="text-sm">{{ formatDate(event.start as string) }}</span>
        </div>
        <div class="flex items-center gap-3 text-slate-600">
          <Clock class="size-4 text-slate-400" />
          <span class="text-sm"
            >{{ formatTime(event.start as string) }} - {{ formatTime(event.end as string) }}</span
          >
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="space-y-1">
          <p class="text-[10px] font-bold text-slate-400 uppercase">Ministère</p>
          <div class="flex items-center gap-2">
            <div
              class="size-2 rounded-full"
              :style="{ backgroundColor: event.backgroundColor }"
            ></div>
            <p class="text-sm font-medium text-slate-700">
              {{ event.extendedProps.ministereLabel }}
            </p>
          </div>
        </div>
        <div class="space-y-1">
          <p class="text-[10px] font-bold text-slate-400 uppercase">Campus</p>
          <p class="text-sm font-medium text-slate-700">{{ event.extendedProps.campus }}</p>
        </div>
      </div>

      <div class="space-y-3">
        <p class="text-[10px] font-bold text-slate-400 uppercase">Équipe Assignée</p>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="member in event.extendedProps.membreIds"
            :key="member"
            class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm"
          >
            <div
              class="flex size-5 items-center justify-center rounded-full bg-slate-100 text-[8px] font-bold"
            >
              {{ member.slice(-2).toUpperCase() }}
            </div>
            {{ member }}
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex gap-3">
        <button
          class="flex-1 rounded-lg bg-(--color-primary-600) px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-(--color-primary-700)"
        >
          Modifier
        </button>
        <button class="px-4 py-2 text-sm font-medium text-slate-600" @click="$emit('close')">
          Fermer
        </button>
      </div>
    </template>
  </AppDrawer>
</template>

<script setup lang="ts">
import { Calendar, Clock } from 'lucide-vue-next'
import type { PlanningEvent } from '../types/planning.types'

defineProps<{ event: PlanningEvent | null }>()
defineEmits(['close'])

const formatDate = (date: string) =>
  new Date(date).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
const formatTime = (date?: string) =>
  date
    ? new Date(date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    : '--:--'
</script>
