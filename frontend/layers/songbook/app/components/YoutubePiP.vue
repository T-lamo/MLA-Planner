<script setup lang="ts">
import { computed, ref } from 'vue'
import { Maximize2, Minimize2, X } from 'lucide-vue-next'

const props = defineProps<{ youtubeUrl: string }>()
const emit = defineEmits<{ close: [] }>()

const isExpanded = ref(false)

/**
 * Extrait le videoId depuis les formats YouTube connus :
 *   youtu.be/ID, watch?v=ID, /embed/ID, /shorts/ID
 */
const videoId = computed<string | null>(() => {
  try {
    const url = new URL(props.youtubeUrl)
    if (url.hostname === 'youtu.be') return url.pathname.slice(1).split('?')[0] ?? null
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
</script>

<template>
  <Teleport to="body">
    <!--
      Un seul bloc — position mobile : bandeau fixe en haut (plein écran)
                      position desktop : flottant bas-droite
    -->
    <div
      class="fixed inset-x-0 top-0 z-10001 shadow-2xl md:inset-x-auto md:top-auto md:right-4 md:bottom-4 md:overflow-hidden md:rounded-2xl md:shadow-[0_8px_32px_rgba(0,0,0,0.35)] md:transition-all md:duration-300 md:ease-out"
      :class="isExpanded ? 'md:w-120' : 'md:w-72'"
    >
      <!-- Barre de titre — desktop uniquement -->
      <div class="hidden items-center justify-between bg-slate-900 px-3 py-2 md:flex">
        <span class="truncate text-xs font-semibold text-slate-300">Vidéo YouTube</span>
        <div class="flex shrink-0 items-center gap-1">
          <button
            type="button"
            class="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white"
            :title="isExpanded ? 'Réduire' : 'Agrandir'"
            @click="isExpanded = !isExpanded"
          >
            <Maximize2 v-if="!isExpanded" class="size-3.5" />
            <Minimize2 v-else class="size-3.5" />
          </button>
          <button
            type="button"
            class="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-red-400"
            title="Fermer la vidéo"
            @click="emit('close')"
          >
            <X class="size-3.5" />
          </button>
        </div>
      </div>

      <!-- Lecteur — unique iframe partagée mobile/desktop -->
      <div class="relative aspect-video w-full bg-black">
        <iframe
          v-if="embedSrc"
          :src="embedSrc"
          class="h-full w-full"
          allow="autoplay; encrypted-media"
          allowfullscreen
          sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
          title="Lecteur YouTube"
        />
        <div v-else class="flex h-full items-center justify-center text-sm text-slate-400">
          Impossible d'extraire l'identifiant vidéo.
        </div>

        <!-- Bouton fermer — mobile uniquement (overlay sur la vidéo) -->
        <button
          type="button"
          class="absolute top-2 right-2 rounded-full bg-black/60 p-1.5 text-white transition-colors hover:bg-black/80 md:hidden"
          title="Fermer la vidéo"
          @click="emit('close')"
        >
          <X class="size-4" />
        </button>
      </div>
    </div>
  </Teleport>
</template>
