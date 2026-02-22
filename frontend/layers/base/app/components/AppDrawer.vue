<template>
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div v-if="isOpen" class="fixed inset-0 z-[10000] flex justify-end">
        <div
          class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
          @click="$emit('close')"
        ></div>

        <Transition name="drawer-slide">
          <aside
            v-if="isOpen"
            class="relative flex h-full w-full max-w-md flex-col bg-white shadow-2xl"
          >
            <div class="flex items-center justify-between border-b border-slate-100 p-4">
              <slot name="header">
                <h3 class="font-bold text-slate-800">{{ title }}</h3>
              </slot>
              <button
                class="rounded-full p-2 transition-colors hover:bg-slate-100"
                @click="$emit('close')"
              >
                <X class="size-5 text-slate-500" />
              </button>
            </div>

            <div class="custom-scrollbar flex-1 overflow-y-auto p-6">
              <slot />
            </div>

            <div v-if="$slots.footer" class="border-t border-slate-100 bg-slate-50 p-4">
              <slot name="footer" />
            </div>
          </aside>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { X } from 'lucide-vue-next'

defineProps<{
  isOpen: boolean
  title?: string
}>()

defineEmits(['close'])
</script>

<style scoped>
.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 0.3s ease;
}
.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}

.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: translateX(100%);
}
</style>
