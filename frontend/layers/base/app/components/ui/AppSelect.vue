<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="block text-xs font-medium text-slate-700">
      {{ label }}
      <span v-if="required" class="ml-0.5 text-red-500" aria-hidden="true">*</span>
    </label>

    <div class="form-select-wrapper">
      <select
        :id="id"
        :value="modelValue"
        :disabled="disabled"
        :class="[
          'form-input',
          'form-select',
          size === 'sm' ? 'form-input-sm' : '',
          error ? 'is-error' : '',
        ]"
        @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option v-if="placeholder" :value="null" disabled :selected="modelValue === null">
          {{ placeholder }}
        </option>
        <option v-for="opt in options" :key="String(opt.value)" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <ChevronDown class="form-select-chevron" />
    </div>

    <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'

withDefaults(
  defineProps<{
    modelValue: string | number | null | undefined
    options: { label: string; value: string | number | null }[]
    placeholder?: string
    label?: string
    id?: string
    disabled?: boolean
    size?: 'sm' | 'md'
    error?: string
    required?: boolean
  }>(),
  {
    placeholder: undefined,
    label: undefined,
    id: undefined,
    disabled: false,
    size: 'md',
    error: undefined,
    required: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>
