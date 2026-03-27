<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { Check, ChevronDown, X } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    modelValue: string[]
    options: { label: string; value: string }[]
    placeholder?: string
    searchable?: boolean
  }>(),
  {
    placeholder: 'Sélectionner…',
    searchable: true,
  },
)

const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>()

const wrapperRef = ref<HTMLElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)
const isOpen = ref(false)
const search = ref('')

// ── Position du dropdown ─────────────────────────────────────────────
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
  if (isOpen.value) return
  updateDropdownPosition()
  isOpen.value = true
  search.value = ''
  if (props.searchable) {
    await nextTick()
    searchInputRef.value?.focus()
  }
}

function close() {
  isOpen.value = false
  search.value = ''
}

// ── Click outside ────────────────────────────────────────────────────
// Le dropdown est téléporté dans <body> → il faut vérifier les DEUX refs
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
function isSelected(val: string) {
  return props.modelValue.includes(val)
}

function getLabel(val: string) {
  return props.options.find((o) => o.value === val)?.label ?? val
}

// ── Toggle / remove ───────────────────────────────────────────────────
function toggle(val: string) {
  if (isSelected(val)) {
    emit(
      'update:modelValue',
      props.modelValue.filter((v) => v !== val),
    )
  } else {
    emit('update:modelValue', [...props.modelValue, val])
  }
}

function remove(val: string) {
  emit(
    'update:modelValue',
    props.modelValue.filter((v) => v !== val),
  )
}
</script>

<template>
  <div ref="wrapperRef" class="relative">
    <!-- ── Trigger ── -->
    <div
      role="combobox"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
      class="form-input flex min-h-[38px] cursor-pointer flex-wrap items-center gap-1.5 py-1.5 pr-8"
      :class="isOpen ? 'border-primary-400 ring-primary-500/20 ring-2' : ''"
      tabindex="0"
      @click="openDropdown"
      @keydown.enter.prevent="openDropdown"
      @keydown.escape="close"
    >
      <!-- Chips sélectionnées -->
      <span
        v-for="val in modelValue"
        :key="val"
        class="bg-primary-50 border-primary-100 inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium text-(--color-primary-700)"
      >
        {{ getLabel(val) }}
        <button
          type="button"
          class="rounded-full hover:text-red-500 focus:outline-none"
          :aria-label="`Retirer ${getLabel(val)}`"
          @click.stop="remove(val)"
        >
          <X class="size-3" />
        </button>
      </span>

      <!-- Input de recherche (quand ouvert) -->
      <input
        v-if="searchable && isOpen"
        ref="searchInputRef"
        v-model="search"
        type="text"
        class="min-w-[80px] flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
        :placeholder="modelValue.length === 0 ? placeholder : 'Rechercher…'"
        @keydown.escape.prevent="close"
        @click.stop
      />

      <!-- Placeholder si vide et fermé -->
      <span v-else-if="!isOpen && modelValue.length === 0" class="text-sm text-slate-400">
        {{ placeholder }}
      </span>

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
          :aria-multiselectable="true"
          :style="dropdownStyle"
          class="custom-scrollbar fixed z-10001 max-h-52 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl"
        >
          <li
            v-for="opt in filteredOptions"
            :key="opt.value"
            role="option"
            :aria-selected="isSelected(opt.value)"
            class="flex cursor-pointer items-center justify-between px-4 py-2.5 text-sm transition-colors hover:bg-slate-50"
            @mousedown.prevent="toggle(opt.value)"
          >
            <span
              :class="
                isSelected(opt.value)
                  ? 'font-semibold text-(--color-primary-700)'
                  : 'text-slate-700'
              "
            >
              {{ opt.label }}
            </span>
            <Check v-if="isSelected(opt.value)" class="text-primary-600 size-4 shrink-0" />
          </li>
          <li v-if="filteredOptions.length === 0" class="px-4 py-3 text-sm text-slate-400">
            Aucun résultat
          </li>
        </ul>
      </Transition>
    </Teleport>
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
