<script setup lang="ts">
import { Eye, EyeOff, Save } from 'lucide-vue-next'
import type { ChantContenuCreate } from '../types/chant'

const props = defineProps<{
  modelValue: string
  tonalite: string
  isSaving?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:tonalite': [value: string]
  save: [payload: ChantContenuCreate]
}>()

const showPreview = ref(false)
const localContent = ref(props.modelValue)
const localTonalite = ref(props.tonalite)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function onInput(e: Event) {
  const val = (e.target as HTMLTextAreaElement).value
  localContent.value = val
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => emit('update:modelValue', val), 400)
}

// Minimum visible lines in the editor
const MIN_LINES = 12
const lineCount = computed(() => Math.max(localContent.value.split('\n').length, MIN_LINES))

// Chord: [G], [Am], [C#m], [F#], [Bb/F], etc.
const CHORD_RE =
  /\[([A-G][#b]?(?:m|maj|min|sus[24]?|add\d|dim|aug)?(?:7|9|11|13)?(?:\/[A-G][#b]?)?)\]/g
// ChordPro directive: {chorus}, {verse}, {title: …}, etc.
const DIRECTIVE_RE = /\{([^}]*)\}/g

/**
 * Safe: user input is fully HTML-escaped (& < >) BEFORE any span injection.
 * Capture groups therefore only contain entity-encoded text — no raw HTML possible.
 * CHORD_RE only matches [A-G#b/...] characters; DIRECTIVE_RE operates on escaped text.
 */
const highlightedContent = computed(() => {
  // 1. Escape all HTML special characters first
  const escaped = localContent.value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 2. Inject hardcoded spans — capture groups are already HTML-safe at this point
  const withChords = escaped.replace(CHORD_RE, '<span class="cp-chord">[$1]</span>')
  const withDirectives = withChords.replace(
    DIRECTIVE_RE,
    (_, p1: string) => `<span class="cp-directive">{${p1.replace(/\$/g, '$$$$')}}</span>`,
  )
  // Trailing newline keeps height in sync with textarea
  return withDirectives + '\n'
})

// Keep local state in sync with parent
watch(
  () => props.modelValue,
  (v) => {
    if (v !== localContent.value) localContent.value = v
  },
)
watch(
  () => props.tonalite,
  (v) => {
    if (v !== localTonalite.value) localTonalite.value = v
  },
)

function handleSave() {
  emit('save', {
    tonalite: localTonalite.value,
    paroles_chords: localContent.value,
  })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- ── Toolbar ── -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <!-- Left: tonality + line counter -->
      <div class="flex items-center gap-4">
        <label class="flex items-center gap-2 text-sm font-medium text-(--color-neutral-700)">
          Tonalité
          <input
            v-model="localTonalite"
            type="text"
            placeholder="G, Am, F#…"
            class="w-20 rounded-md border border-(--color-neutral-300) px-2 py-1 text-sm focus:border-(--color-primary-400) focus:outline-none"
            @change="emit('update:tonalite', localTonalite)"
          />
        </label>
        <span class="text-xs text-(--color-neutral-400)">
          {{ localContent.split('\n').length }}
          ligne{{ localContent.split('\n').length > 1 ? 's' : '' }}
        </span>
      </div>

      <!-- Right: preview toggle + save -->
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 rounded-md border border-(--color-neutral-200) bg-white px-3 py-1.5 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50)"
          @click="showPreview = !showPreview"
        >
          <EyeOff v-if="showPreview" class="h-4 w-4" />
          <Eye v-else class="h-4 w-4" />
          {{ showPreview ? 'Éditeur' : 'Aperçu' }}
        </button>
        <button
          type="button"
          :disabled="isSaving"
          class="inline-flex items-center gap-1.5 rounded-md bg-(--color-primary-600) px-3 py-1.5 text-sm font-medium text-white hover:bg-(--color-primary-700) disabled:opacity-50"
          @click="handleSave"
        >
          <Save class="h-4 w-4" />
          {{ isSaving ? 'Sauvegarde…' : 'Enregistrer' }}
        </button>
      </div>
    </div>

    <!-- ── Preview mode ── -->
    <div v-if="showPreview" class="rounded-xl border border-(--color-neutral-200) bg-white p-6">
      <ChantContenuViewer
        :contenu="{
          id: '',
          chant_id: '',
          tonalite: localTonalite,
          paroles_chords: localContent,
          version: 1,
          date_modification: new Date().toISOString(),
        }"
      />
    </div>

    <!-- ── Editor mode ── -->
    <div
      v-else
      class="overflow-hidden rounded-xl border border-(--color-neutral-700) bg-(--color-neutral-950) font-mono text-sm leading-5"
    >
      <div class="flex">
        <!-- Line numbers -->
        <div
          class="border-r border-(--color-neutral-800) bg-(--color-neutral-900) px-3 py-3 text-right text-xs text-(--color-neutral-500) select-none"
          aria-hidden="true"
        >
          <div v-for="n in lineCount" :key="n" class="leading-5">{{ n }}</div>
        </div>

        <!-- Code area: mirror + textarea stacked -->
        <div class="relative flex-1 overflow-auto">
          <!-- Syntax-highlighted mirror (non-interactive) -->
          <!-- Content is HTML-escaped (&, <, >) before any span injection — XSS-safe -->
          <!-- eslint-disable vue/no-v-html -->
          <pre
            aria-hidden="true"
            class="pointer-events-none absolute inset-0 px-4 py-3 text-sm leading-5 break-words whitespace-pre-wrap text-(--color-neutral-100)"
            v-html="highlightedContent"
          />
          <!-- eslint-enable vue/no-v-html -->
          <!-- Transparent textarea (captures input, shows caret) -->
          <textarea
            :value="localContent"
            spellcheck="false"
            autocomplete="off"
            class="relative z-10 w-full resize-none bg-transparent px-4 py-3 text-sm leading-5 text-transparent caret-white focus:outline-none"
            :style="{ minHeight: `${lineCount * 1.25 + 1.5}rem` }"
            @input="onInput"
          />
        </div>
      </div>
    </div>

    <!-- Syntax hint -->
    <p class="text-xs text-(--color-neutral-400)">
      Syntaxe ChordPro :
      <code class="rounded bg-(--color-neutral-100) px-1 text-xs">[Sol]</code>
      pour les accords,
      <code class="rounded bg-(--color-neutral-100) px-1 text-xs">{chorus}</code>
      pour les sections.
    </p>
  </div>
</template>

<style scoped>
@reference "~~/layers/base/app/assets/css/main.css";

/* Chord tokens highlighted in the mirror */
:deep(.cp-chord) {
  color: var(--color-primary-400);
  font-weight: 600;
}

/* Directive tokens ({chorus}, {verse}, …) */
:deep(.cp-directive) {
  color: var(--color-amber-400);
  font-style: italic;
}
</style>
