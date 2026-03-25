<script setup lang="ts">
import { onUnmounted, ref } from 'vue'
import { CalendarRange, Copy, MoreHorizontal, Pencil, Trash2 } from 'lucide-vue-next'
import type { PlanningTemplateListItem } from '../types/planning.types'

defineProps<{ template: PlanningTemplateListItem }>()

const emit = defineEmits<{
  edit: []
  duplicate: []
  'generate-serie': []
  delete: []
}>()

const isOpen = ref(false)
const triggerRef = ref<HTMLButtonElement | null>(null)
const menuRef = ref<HTMLDivElement | null>(null)
const menuPos = ref({ top: 0, left: 0 })

function open() {
  if (!triggerRef.value) return
  // Close any other open instance first
  document.dispatchEvent(new CustomEvent('template-menu:close-all'))
  const rect = triggerRef.value.getBoundingClientRect()
  menuPos.value = {
    top: rect.bottom + window.scrollY + 4,
    left: rect.right + window.scrollX - 192,
  }
  isOpen.value = true
}

function closeAll() {
  isOpen.value = false
}

function close(e: MouseEvent) {
  const target = e.target as Node
  const inTrigger = triggerRef.value?.contains(target) ?? false
  const inMenu = menuRef.value?.contains(target) ?? false
  if (!inTrigger && !inMenu) {
    isOpen.value = false
  }
}

function doEdit() {
  emit('edit')
  isOpen.value = false
}
function doDuplicate() {
  emit('duplicate')
  isOpen.value = false
}
function doGenerateSerie() {
  emit('generate-serie')
  isOpen.value = false
}
function doDelete() {
  emit('delete')
  isOpen.value = false
}

document.addEventListener('click', close)
document.addEventListener('template-menu:close-all', closeAll)
onUnmounted(() => {
  document.removeEventListener('click', close)
  document.removeEventListener('template-menu:close-all', closeAll)
})
</script>

<template>
  <div>
    <button
      ref="triggerRef"
      type="button"
      class="rounded-lg p-1.5 text-(--color-neutral-400) hover:bg-(--color-neutral-100) hover:text-(--color-neutral-700)"
      @click.stop="isOpen ? (isOpen = false) : open()"
    >
      <MoreHorizontal class="size-4" />
    </button>

    <Teleport to="body">
      <div
        v-if="isOpen"
        ref="menuRef"
        :style="{ top: `${menuPos.top}px`, left: `${menuPos.left}px` }"
        class="absolute z-[9999] w-48 rounded-xl border border-(--color-neutral-200) bg-white py-1 shadow-lg"
      >
        <button
          class="flex w-full items-center gap-2 px-3 py-2 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50)"
          @click="doEdit"
        >
          <Pencil class="size-4" /> Modifier
        </button>
        <button
          class="flex w-full items-center gap-2 px-3 py-2 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50)"
          @click="doDuplicate"
        >
          <Copy class="size-4" /> Dupliquer
        </button>
        <button
          class="flex w-full items-center gap-2 px-3 py-2 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50)"
          @click="doGenerateSerie"
        >
          <CalendarRange class="size-4" /> Générer une série
        </button>
        <hr class="my-1 border-(--color-neutral-100)" />
        <button
          class="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
          @click="doDelete"
        >
          <Trash2 class="size-4" /> Supprimer
        </button>
      </div>
    </Teleport>
  </div>
</template>
