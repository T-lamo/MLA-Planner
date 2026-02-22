<script setup lang="ts">
import { CircleCheck, CircleAlert, Info, TriangleAlert, X } from 'lucide-vue-next'
import { useMLANotificationStore } from '../stores/useMLANotificationStore'

const store = useMLANotificationStore()

const icons = {
  success: CircleCheck,
  error: CircleAlert,
  warning: TriangleAlert,
  info: Info,
}

const styles = {
  success: 'border-green-500/50 bg-green-50/90 text-green-900',
  error: 'border-red-500/50 bg-red-50/90 text-red-900',
  warning: 'border-amber-500/50 bg-amber-50/90 text-amber-900',
  info: 'border-blue-500/50 bg-blue-50/90 text-blue-900',
}
</script>

<template>
  <div
    class="pointer-events-none fixed inset-x-0 bottom-4 z-[100] flex flex-col items-center gap-3 px-4 sm:px-6 md:top-4 md:right-4 md:bottom-auto md:left-auto md:w-full md:max-w-sm md:items-end"
  >
    <TransitionGroup
      enterActiveClass="transition duration-300 ease-out"
      enterFromClass="translate-y-4 md:translate-y-0 md:translate-x-12 opacity-0"
      enterToClass="translate-y-0 md:translate-x-0 opacity-100"
      leaveActiveClass="transition duration-200 ease-in"
      leaveFromClass="opacity-100 scale-100"
      leaveToClass="opacity-0 scale-95"
    >
      <div
        v-for="n in store.notifications"
        :key="n.id"
        class="group pointer-events-auto relative flex w-full max-w-md gap-3 overflow-hidden rounded-xl border p-4 shadow-2xl backdrop-blur-md md:max-w-none"
        :class="styles[n.type]"
        @mouseenter="store.pauseTimer(n.id)"
        @mouseleave="store.resumeTimer(n.id)"
      >
        <component :is="icons[n.type]" class="size-5 shrink-0 opacity-80" />

        <div class="flex-1">
          <h4 class="text-sm leading-tight font-bold">{{ n.title }}</h4>
          <p v-if="n.description" class="mt-1 text-xs leading-relaxed font-medium opacity-80">
            {{ n.description }}
          </p>
        </div>

        <button
          class="shrink-0 rounded-lg p-1 transition-colors hover:bg-black/5 md:opacity-0 md:group-hover:opacity-100"
          @click="store.remove(n.id)"
        >
          <X class="size-4" />
        </button>

        <div
          v-if="!n.persistent"
          class="absolute bottom-0 left-0 h-1 bg-current opacity-10 transition-all duration-[5000ms] ease-linear"
          :style="{ width: n.isPaused ? '100%' : '0%' }"
        />
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
/* Assure une lecture fluide des transitions sur les listes */
.v-move {
  transition: transform 0.4s ease;
}
</style>
