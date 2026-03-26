<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="block text-xs font-medium text-slate-700">
      {{ label }}
      <span v-if="required" class="ml-0.5 text-red-500" aria-hidden="true">*</span>
    </label>

    <div :class="hasLeadingIcon ? 'form-input-wrapper' : undefined">
      <span v-if="hasLeadingIcon" class="form-input-icon">
        <slot name="leading-icon" />
      </span>
      <slot />
    </div>

    <p v-if="error" :id="errorId" class="text-xs text-red-500">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-slate-400">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue'

const props = withDefaults(
  defineProps<{
    label?: string
    id?: string
    error?: string
    hint?: string
    required?: boolean
  }>(),
  {
    label: undefined,
    id: undefined,
    error: undefined,
    hint: undefined,
    required: false,
  },
)

const slots = useSlots()

const hasLeadingIcon = computed(() => !!slots['leading-icon'])
const errorId = computed(() => (props.id ? `${props.id}-error` : undefined))
</script>
