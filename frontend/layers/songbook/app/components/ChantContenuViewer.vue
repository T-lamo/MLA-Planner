<script setup lang="ts">
import type { ChantContenuRead } from '../types/chant'

const props = defineProps<{
  contenu: ChantContenuRead
  transposePreview?: string | null
  showChords?: boolean
}>()

// Affiche le contenu transposé si disponible, sinon l'original
const displayContent = computed(() => props.transposePreview ?? props.contenu.paroles_chords)

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// Convertit le format ChordPro en lignes HTML : accords au-dessus du texte
function renderChordPro(raw: string, withChords: boolean): string {
  return raw
    .split('\n')
    .map((line) => {
      if (!line.includes('[')) return `<p class="lyric-line">${escapeHtml(line)}</p>`
      if (!withChords) {
        // Supprime les marqueurs d'accords et n'affiche que les paroles
        const lyricOnly = line.replace(/\[[^\]]*\]/g, '')
        return `<p class="lyric-line">${escapeHtml(lyricOnly)}</p>`
      }
      let chordLine = ''
      let lyricLine = ''
      let i = 0
      while (i < line.length) {
        if (line[i] === '[') {
          const end = line.indexOf(']', i)
          if (end === -1) {
            lyricLine += line[i]
            i++
            continue
          }
          const chord = line.slice(i + 1, end)
          chordLine += `<span class="chord">${escapeHtml(chord)}</span>`
          lyricLine +=
            '<span class="chord-placeholder">' + '\u00a0'.repeat(chord.length + 1) + '</span>'
          i = end + 1
        } else {
          chordLine += '<span class="lyric-spacer">&nbsp;</span>'
          lyricLine += escapeHtml(line[i] as string)
          i++
        }
      }
      return `<span class="chord-row">${chordLine}</span><span class="lyric-row">${lyricLine}</span>`
    })
    .join('\n')
}

const rendered = computed(() => renderChordPro(displayContent.value, props.showChords ?? true))
</script>

<template>
  <div class="chant-contenu-viewer font-mono text-sm leading-6 whitespace-pre-wrap">
    <div class="mb-2 flex items-center gap-2">
      <span class="text-xs font-semibold tracking-wide text-(--color-primary-700) uppercase">
        Tonalité :
      </span>
      <span class="font-bold">{{ contenu.tonalite }}</span>
      <span v-if="transposePreview" class="text-xs text-(--color-warning-600)"
        >(aperçu transposé)</span
      >
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div class="chord-sheet" v-html="rendered" />
  </div>
</template>

<style scoped>
@reference "../../../base/app/assets/css/main.css";

.chord-sheet {
  @apply leading-7;
}

.chord-sheet :deep(.chord-row) {
  @apply block font-semibold text-(--color-primary-600);
}

.chord-sheet :deep(.lyric-row) {
  @apply mb-3 block text-(--color-neutral-800);
}

.chord-sheet :deep(.chord) {
  @apply mr-1 inline-block min-w-[2rem];
}

.chord-sheet :deep(.lyric-line) {
  @apply mb-1 text-(--color-neutral-700);
}
</style>
