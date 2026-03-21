<script setup lang="ts">
import { ChevronDown, ChevronUp, RotateCcw } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: number
  originalKey: string
  previewKey?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [v: number]
}>()

function increment() {
  if (props.modelValue < 12) emit('update:modelValue', props.modelValue + 1)
}

function decrement() {
  if (props.modelValue > -12) emit('update:modelValue', props.modelValue - 1)
}

function reset() {
  emit('update:modelValue', 0)
}
</script>

<template>
  <div class="flex items-center gap-3 rounded-lg bg-(--color-neutral-50) px-4 py-2">
    <span class="text-xs font-medium text-(--color-neutral-600)">Transposer :</span>

    <div class="flex items-center gap-1">
      <button
        type="button"
        class="rounded p-1 text-(--color-neutral-500) hover:bg-(--color-neutral-200)"
        :disabled="modelValue <= -12"
        @click="decrement"
      >
        <ChevronDown class="h-4 w-4" />
      </button>

      <span class="w-8 text-center font-mono font-semibold text-(--color-neutral-800)">
        {{ modelValue > 0 ? `+${modelValue}` : modelValue }}
      </span>

      <button
        type="button"
        class="rounded p-1 text-(--color-neutral-500) hover:bg-(--color-neutral-200)"
        :disabled="modelValue >= 12"
        @click="increment"
      >
        <ChevronUp class="h-4 w-4" />
      </button>
    </div>

    <div class="flex items-center gap-1 text-sm">
      <span class="font-medium text-(--color-neutral-700)">{{ originalKey }}</span>
      <span v-if="modelValue !== 0 && previewKey" class="text-(--color-primary-600)">
        → {{ previewKey }}
      </span>
    </div>

    <button
      v-if="modelValue !== 0"
      type="button"
      class="ml-auto flex items-center gap-1 rounded px-2 py-1 text-xs text-(--color-neutral-500) hover:bg-(--color-neutral-200)"
      @click="reset"
    >
      <RotateCcw class="h-3 w-3" />
      Réinitialiser
    </button>
  </div>
</template>
