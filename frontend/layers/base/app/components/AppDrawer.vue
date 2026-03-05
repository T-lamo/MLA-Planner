<template>
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div v-if="isOpen" class="fixed inset-0 z-[10000] flex justify-end">
        <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="handleClose"></div>

        <Transition name="drawer-slide">
          <aside
            v-if="isOpen"
            :class="[
              'relative flex h-full flex-col bg-white shadow-2xl transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]',
              sizeClasses,
            ]"
            role="dialog"
            :aria-label="title"
            aria-modal="true"
          >
            <div class="flex items-center justify-between border-b border-slate-100 p-4">
              <div class="flex items-center gap-2">
                <slot name="header">
                  <h3 class="truncate font-bold text-slate-800">{{ title }}</h3>
                </slot>
              </div>

              <div class="flex items-center gap-1">
                <button
                  v-if="isOpen"
                  class="hidden rounded-full p-2 text-slate-500 transition-colors hover:bg-slate-100 md:flex"
                  :title="expandTitle"
                  @click="toggleExpand"
                >
                  <component :is="expandIcon" class="size-4" />
                </button>

                <button
                  class="rounded-full p-2 text-slate-500 transition-colors hover:bg-slate-100"
                  @click="handleClose"
                >
                  <X class="size-5" />
                </button>
              </div>
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
import { ref, computed, watch } from 'vue'
import { X, Maximize2, Minimize2 } from 'lucide-vue-next'

// Types pour les tailles
type DrawerSize = 'standard' | 'half' | 'full'

const props = defineProps<{
  isOpen: boolean
  title?: string
  initialSize?: DrawerSize
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'size-change', size: DrawerSize): void
}>()

// État interne de la taille
const currentSize = ref<DrawerSize>(props.initialSize || 'standard')

// Calcul des classes de largeur
const sizeClasses = computed(() => {
  return {
    'w-full md:max-w-md': currentSize.value === 'standard',
    'w-full md:w-1/2': currentSize.value === 'half',
    'w-full': currentSize.value === 'full',
  }
})

// Logique du bouton d'expansion (cycle : standard -> half -> full -> standard)
const toggleExpand = () => {
  if (currentSize.value === 'standard') currentSize.value = 'half'
  else if (currentSize.value === 'half') currentSize.value = 'full'
  else currentSize.value = 'standard'

  emit('size-change', currentSize.value)
}

// Icone dynamique selon l'état
const expandIcon = computed(() => {
  if (currentSize.value === 'full') return Minimize2
  return Maximize2
})

const expandTitle = computed(() => {
  if (currentSize.value === 'standard') return 'Agrandir (50%)'
  if (currentSize.value === 'half') return 'Plein écran'
  return 'Réduire'
})

// Reset de la taille à la fermeture pour retrouver l'état initial à la prochaine ouverture
const handleClose = () => {
  emit('close')
  // Optionnel : décommenter pour reset la taille à chaque fermeture
  // setTimeout(() => currentSize.value = 'standard', 300)
}

// Bloquer le scroll du body quand le drawer est ouvert
watch(
  () => props.isOpen,
  (val) => {
    if (typeof document !== 'undefined') {
      document.body.style.overflow = val ? 'hidden' : ''
    }
  },
)
</script>

<style scoped>
@reference "../assets/css/main.css";
/* Transition Fade pour l'overlay */
.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 0.3s ease;
}
.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}

/* Transition Slide pour l'entrée/sortie du drawer */
.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: translateX(100%);
}

/* Scrollbar personnalisée pour le body du drawer */
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  @apply bg-transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  @apply rounded-full bg-slate-200 hover:bg-slate-300;
}
</style>
