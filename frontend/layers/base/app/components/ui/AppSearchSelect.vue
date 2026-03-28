<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { Check, ChevronDown, X } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    modelValue: string
    options: { label: string; value: string }[]
    placeholder?: string
    label?: string
    error?: string
    required?: boolean
    disabled?: boolean
  }>(),
  {
    placeholder: 'Sélectionner…',
    label: undefined,
    error: undefined,
    required: false,
    disabled: false,
  },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const wrapperRef = ref<HTMLElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)
const isOpen = ref(false)
const search = ref('')

// ── Position du dropdown (Teleport) ──────────────────────────────────
const dropdownStyle = ref<Record<string, string>>({})

function updateDropdownPosition() {
  if (!wrapperRef.value) return
  const rect = wrapperRef.value.getBoundingClientRect()
  dropdownStyle.value = {
    top: `${rect.bottom + 4}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
  }
}

// ── Ouverture / fermeture ─────────────────────────────────────────────
async function openDropdown() {
  if (isOpen.value || props.disabled) return
  updateDropdownPosition()
  isOpen.value = true
  search.value = ''
  await nextTick()
  searchInputRef.value?.focus()
}

function close() {
  isOpen.value = false
  search.value = ''
}

// ── Click outside ────────────────────────────────────────────────────
function onMouseDown(e: MouseEvent) {
  const t = e.target as Node
  const insideTrigger = wrapperRef.value?.contains(t) ?? false
  const insideDropdown = dropdownRef.value?.contains(t) ?? false
  if (!insideTrigger && !insideDropdown) close()
}
onMounted(() => document.addEventListener('mousedown', onMouseDown))
onUnmounted(() => document.removeEventListener('mousedown', onMouseDown))

// ── Filtrage ─────────────────────────────────────────────────────────
const filteredOptions = computed(() => {
  if (!search.value) return props.options
  const q = search.value.toLowerCase()
  return props.options.filter((o) => o.label.toLowerCase().includes(q))
})

// ── Helpers ──────────────────────────────────────────────────────────
const selectedLabel = computed(
  () => props.options.find((o) => o.value === props.modelValue)?.label ?? '',
)

function select(val: string) {
  emit('update:modelValue', val)
  close()
}

function clear() {
  emit('update:modelValue', '')
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" class="block text-xs font-medium text-slate-700">
      {{ label }}
      <span v-if="required" class="ml-0.5 text-red-500" aria-hidden="true">*</span>
    </label>

    <div ref="wrapperRef" class="relative">
      <!-- ── Trigger ── -->
      <div
        role="combobox"
        :aria-expanded="isOpen"
        aria-haspopup="listbox"
        class="form-input flex h-9.5 cursor-pointer items-center gap-2 overflow-hidden py-2 pr-8"
        :class="[
          isOpen ? 'border-primary-400 ring-primary-500/20 ring-2' : '',
          error ? 'is-error' : '',
          disabled ? 'cursor-not-allowed opacity-50' : '',
        ]"
        tabindex="0"
        @click="openDropdown"
        @keydown.enter.prevent="openDropdown"
        @keydown.escape="close"
      >
        <!-- Input de recherche (quand ouvert) -->
        <input
          v-if="isOpen"
          ref="searchInputRef"
          v-model="search"
          type="text"
          class="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
          placeholder="Rechercher…"
          @keydown.escape.prevent="close"
          @click.stop
        />

        <!-- Valeur sélectionnée (quand fermé) -->
        <span v-else-if="selectedLabel" class="flex-1 truncate text-sm text-slate-800">
          {{ selectedLabel }}
        </span>

        <!-- Placeholder -->
        <span v-else class="flex-1 text-sm text-slate-400">{{ placeholder }}</span>

        <!-- Bouton clear -->
        <button
          v-if="modelValue && !isOpen"
          type="button"
          class="absolute top-1/2 right-7 -translate-y-1/2 rounded p-0.5 text-slate-400 hover:text-slate-600"
          :aria-label="`Effacer la sélection`"
          @click.stop="clear"
        >
          <X class="size-3.5" />
        </button>

        <!-- Chevron -->
        <ChevronDown
          class="pointer-events-none absolute top-1/2 right-2.5 size-4 -translate-y-1/2 text-slate-400 transition-transform duration-200"
          :class="isOpen ? 'rotate-180' : ''"
        />
      </div>

      <!-- ── Dropdown (Teleport) ── -->
      <Teleport to="body">
        <Transition
          enterActiveClass="transition-all duration-150 ease-out"
          enterFromClass="opacity-0 -translate-y-1"
          enterToClass="opacity-100 translate-y-0"
          leaveActiveClass="transition-all duration-100 ease-in"
          leaveFromClass="opacity-100 translate-y-0"
          leaveToClass="opacity-0 -translate-y-1"
        >
          <ul
            v-if="isOpen"
            ref="dropdownRef"
            role="listbox"
            :style="dropdownStyle"
            class="custom-scrollbar fixed z-10001 max-h-52 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl"
          >
            <li
              v-for="opt in filteredOptions"
              :key="opt.value"
              role="option"
              :aria-selected="opt.value === modelValue"
              class="flex cursor-pointer items-center justify-between px-4 py-2.5 text-sm transition-colors hover:bg-slate-50"
              @mousedown.prevent="select(opt.value)"
            >
              <span
                :class="
                  opt.value === modelValue
                    ? 'font-semibold text-(--color-primary-700)'
                    : 'text-slate-700'
                "
              >
                {{ opt.label }}
              </span>
              <Check v-if="opt.value === modelValue" class="text-primary-600 size-4 shrink-0" />
            </li>
            <li v-if="filteredOptions.length === 0" class="px-4 py-3 text-sm text-slate-400">
              Aucun résultat
            </li>
          </ul>
        </Transition>
      </Teleport>
    </div>

    <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
  </div>
</template>

<style scoped>
@reference "../../assets/css/main.css";

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
</style>
