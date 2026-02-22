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
  success: 'border-green-500/50 bg-green-50/80 text-green-900',
  error: 'border-red-500/50 bg-red-50/80 text-red-900',
  warning: 'border-amber-500/50 bg-amber-50/80 text-amber-900',
  info: 'border-blue-500/50 bg-blue-50/80 text-blue-900',
}
</script>

<template>
  <div class="pointer-events-none fixed top-4 right-4 z-100 flex w-full max-w-sm flex-col gap-3">
    <TransitionGroup
      enterActiveClass="transition duration-300 ease-out"
      enterFromClass="translate-x-12 opacity-0"
      enterToClass="translate-x-0 opacity-100"
      leaveActiveClass="transition duration-200 ease-in"
      leaveFromClass="opacity-100 scale-100"
      leaveToClass="opacity-0 scale-95"
    >
      <div
        v-for="n in store.notifications"
        :key="n.id"
        class="group pointer-events-auto relative flex gap-3 overflow-hidden rounded-xl border p-4 shadow-xl backdrop-blur-md"
        :class="styles[n.type]"
        @mouseenter="store.pauseTimer(n.id)"
        @mouseleave="store.resumeTimer(n.id)"
      >
        <component :is="icons[n.type]" class="size-5 shrink-0 opacity-80" />

        <div class="flex-1">
          <h4 class="text-sm leading-none font-semibold">{{ n.title }}</h4>
          <p v-if="n.description" class="mt-1.5 text-xs leading-relaxed opacity-70">
            {{ n.description }}
          </p>
        </div>

        <button
          class="shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
          @click="store.remove(n.id)"
        >
          <X class="size-4" />
        </button>

        <div
          v-if="!n.persistent"
          class="absolute bottom-0 left-0 h-0.5 bg-current opacity-20 transition-all duration-[5000ms] ease-linear"
          :style="{ width: n.isPaused ? '100%' : '0%' }"
        />
      </div>
    </TransitionGroup>
  </div>
</template>
