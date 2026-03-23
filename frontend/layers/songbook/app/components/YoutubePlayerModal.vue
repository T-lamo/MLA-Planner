<script setup lang="ts">
import { X } from 'lucide-vue-next'

const props = defineProps<{
  youtubeUrl: string
}>()

const emit = defineEmits<{
  close: []
}>()

/**
 * Extrait le videoId depuis les formats YouTube connus :
 *   youtu.be/ID, watch?v=ID, /embed/ID, /shorts/ID
 */
const videoId = computed<string | null>(() => {
  try {
    const url = new URL(props.youtubeUrl)
    if (url.hostname === 'youtu.be') {
      return url.pathname.slice(1).split('?')[0] ?? null
    }
    const v = url.searchParams.get('v')
    if (v) return v
    const segments = url.pathname.split('/')
    const idx = segments.findIndex((s) => s === 'embed' || s === 'shorts')
    if (idx !== -1) return segments[idx + 1] ?? null
  } catch {
    // URL invalide
  }
  return null
})

const embedSrc = computed(() =>
  videoId.value ? `https://www.youtube-nocookie.com/embed/${videoId.value}?autoplay=1&rel=0` : null,
)

function onBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 flex items-center justify-center bg-black/70"
      style="z-index: 20000"
      @click="onBackdropClick"
    >
      <div class="relative w-full max-w-3xl px-4">
        <!-- Bouton fermer -->
        <button
          type="button"
          class="absolute -top-10 right-4 flex items-center gap-1.5 rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white hover:bg-white/20"
          @click="emit('close')"
        >
          <X class="h-4 w-4" />
          Fermer
        </button>

        <!-- Lecteur -->
        <div v-if="embedSrc" class="aspect-video w-full overflow-hidden rounded-2xl">
          <iframe
            :src="embedSrc"
            class="h-full w-full"
            allow="autoplay; encrypted-media"
            allowfullscreen
            sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
            title="Lecteur YouTube"
          />
        </div>

        <div
          v-else
          class="flex aspect-video w-full items-center justify-center rounded-2xl bg-black text-sm text-white"
        >
          Impossible d'extraire l'identifiant vidéo.
        </div>
      </div>
    </div>
  </Teleport>
</template>
