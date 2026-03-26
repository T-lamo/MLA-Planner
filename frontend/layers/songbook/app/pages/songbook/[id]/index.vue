<script setup lang="ts">
import { ArrowLeft, Music2, AlignLeft, Pencil, ChevronRight, Youtube } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { useUIStore } from '~~/layers/base/app/stores/useUiStore'
import type { ChantTransposeResponse } from '../../../types/chant'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUIStore()
const campusId = computed(() => uiStore.selectedCampusId ?? '')

const id = computed<string>(() => {
  const raw = route.params.id
  if (Array.isArray(raw)) return raw[0] ?? ''
  return raw ?? ''
})

const {
  categories,
  chants,
  selectedChant,
  isLoading,
  selectChant,
  transpose,
  loadCategories,
  loadChants,
} = useSongbook()

// ── Lecteur YouTube ────────────────────────────────────────────────────────
const showYoutubePlayer = ref(false)

// ── Toggle accords/paroles ─────────────────────────────────────────────────
const showChords = ref(true)

// ── Transposition ──────────────────────────────────────────────────────────
const semitones = ref(0)
const transposePreview = ref<ChantTransposeResponse | null>(null)

watch(semitones, async (v) => {
  if (!selectedChant.value?.contenu || v === 0) {
    transposePreview.value = null
    return
  }
  transposePreview.value = await transpose(id.value, v)
})

watch(showChords, (v) => {
  if (!v) {
    semitones.value = 0
    transposePreview.value = null
  }
})

// ── Catégorie du chant ─────────────────────────────────────────────────────
const chantCategorie = computed(
  () =>
    selectedChant.value?.categorie ??
    categories.value.find((c) => c.code === selectedChant.value?.categorie_code),
)

// ── État 404 ──────────────────────────────────────────────────────────────
const notFound = ref(false)

onMounted(async () => {
  if (categories.value.length === 0) await loadCategories()
  if (chants.value.length === 0) await loadChants(campusId.value)
  try {
    await selectChant(id.value)
    if (!selectedChant.value) notFound.value = true
  } catch {
    notFound.value = true
  }
})
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-8">
    <!-- ── Breadcrumb + actions ───────────────────────────────────────── -->
    <div class="mb-6 flex items-center justify-between">
      <nav class="flex items-center gap-1.5 text-sm text-(--color-neutral-500)">
        <NuxtLink to="/songbook" class="hover:text-(--color-neutral-700)">Songbook</NuxtLink>
        <ChevronRight class="h-3.5 w-3.5 shrink-0" />
        <NuxtLink
          :to="
            chantCategorie
              ? `/songbook/browse?categorie=${chantCategorie.code}`
              : '/songbook/browse'
          "
          class="hover:text-(--color-neutral-700)"
        >
          {{ chantCategorie?.libelle ?? 'Tous les chants' }}
        </NuxtLink>
        <ChevronRight class="h-3.5 w-3.5 shrink-0" />
        <span class="max-w-[160px] truncate text-(--color-neutral-800)">
          {{ selectedChant?.titre ?? '…' }}
        </span>
      </nav>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 rounded-lg border border-(--color-neutral-200) bg-white px-3 py-1.5 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50)"
          @click="router.back()"
        >
          <ArrowLeft class="h-4 w-4" />
          Retour
        </button>
        <NuxtLink
          v-if="authStore.canManageChants && selectedChant"
          :to="`/songbook/${id}/edit`"
          class="inline-flex items-center gap-1.5 rounded-lg border border-(--color-neutral-200) bg-white px-3 py-1.5 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50)"
        >
          <Pencil class="h-4 w-4" />
          Modifier
        </NuxtLink>
      </div>
    </div>

    <!-- ── Loading skeleton ───────────────────────────────────────────── -->
    <div v-if="isLoading && !selectedChant" class="space-y-4">
      <div class="h-9 w-2/3 animate-pulse rounded-lg bg-(--color-neutral-100)" />
      <div class="h-5 w-1/3 animate-pulse rounded-lg bg-(--color-neutral-100)" />
      <div class="mt-6 h-64 animate-pulse rounded-2xl bg-(--color-neutral-100)" />
    </div>

    <!-- ── 404 ────────────────────────────────────────────────────────── -->
    <div v-else-if="notFound" class="flex flex-col items-center gap-4 py-20 text-center">
      <p class="text-lg font-semibold text-(--color-neutral-700)">Chant introuvable</p>
      <p class="text-sm text-(--color-neutral-400)">Ce chant n'existe pas ou a été supprimé.</p>
      <NuxtLink to="/songbook/browse" class="btn btn-primary"> Retour au répertoire </NuxtLink>
    </div>

    <!-- ── Contenu du chant ───────────────────────────────────────────── -->
    <div v-else-if="selectedChant" class="space-y-6">
      <!-- En-tête -->
      <div class="flex items-start justify-between gap-4">
        <div class="min-w-0">
          <h1 class="text-3xl font-bold text-(--color-neutral-900)">{{ selectedChant.titre }}</h1>
          <p v-if="selectedChant.artiste" class="mt-1 text-lg text-(--color-neutral-500)">
            {{ selectedChant.artiste }}
          </p>
          <span
            v-if="chantCategorie"
            class="mt-2 inline-block rounded-full bg-(--color-primary-100) px-3 py-0.5 text-xs font-medium text-(--color-primary-700)"
          >
            {{ chantCategorie.libelle }}
          </span>
        </div>

        <!-- Toggle accords / paroles -->
        <div
          class="flex shrink-0 items-center gap-1 rounded-lg border border-(--color-neutral-200) bg-(--color-neutral-50) p-1"
        >
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
            :class="
              showChords
                ? 'bg-white text-(--color-neutral-900)'
                : 'text-(--color-neutral-500) hover:text-(--color-neutral-700)'
            "
            @click="showChords = true"
          >
            <Music2 class="h-3.5 w-3.5" />
            Accords
          </button>
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
            :class="
              !showChords
                ? 'bg-white text-(--color-neutral-900)'
                : 'text-(--color-neutral-500) hover:text-(--color-neutral-700)'
            "
            @click="showChords = false"
          >
            <AlignLeft class="h-3.5 w-3.5" />
            Paroles
          </button>
        </div>
      </div>

      <!-- ── Lecteur YouTube ──────────────────────────────────────────── -->
      <div
        v-if="selectedChant.youtube_url"
        class="flex items-center gap-3 rounded-2xl border border-(--color-red-100) bg-(--color-red-50) px-5 py-4"
      >
        <Youtube class="h-5 w-5 shrink-0 text-(--color-red-500)" />
        <span class="flex-1 text-sm font-medium text-(--color-red-700)">
          Une vidéo YouTube est disponible pour ce chant
        </span>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 rounded-lg bg-(--color-red-600) px-4 py-2 text-sm font-medium text-white hover:bg-(--color-red-700)"
          @click="showYoutubePlayer = true"
        >
          <Youtube class="h-4 w-4" />
          Regarder
        </button>
      </div>
      <div
        v-else-if="authStore.canManageChants"
        class="flex items-center gap-3 rounded-2xl border border-(--color-neutral-200) bg-(--color-neutral-50) px-5 py-4"
      >
        <Youtube class="h-5 w-5 shrink-0 text-(--color-neutral-400)" />
        <span class="flex-1 text-sm text-(--color-neutral-500)"
          >Aucun lien YouTube pour ce chant</span
        >
        <NuxtLink
          :to="`/songbook/${id}/edit`"
          class="text-sm text-(--color-primary-600) hover:text-(--color-primary-700) hover:underline"
        >
          Ajouter
        </NuxtLink>
      </div>

      <!-- Contrôle transposition (accords uniquement) -->
      <ChantTransposeControl
        v-if="showChords && selectedChant.contenu"
        v-model="semitones"
        :originalKey="selectedChant.contenu.tonalite"
        :previewKey="transposePreview?.tonalite_transposee"
      />

      <!-- Contenu -->
      <div
        v-if="selectedChant.contenu"
        class="rounded-2xl border border-(--color-neutral-200) bg-white p-8"
      >
        <ChantContenuViewer
          :contenu="selectedChant.contenu"
          :transposePreview="transposePreview?.paroles_chords"
          :showChords="showChords"
        />
      </div>

      <div
        v-else
        class="rounded-2xl border border-(--color-neutral-200) bg-white p-8 text-center text-sm text-(--color-neutral-400)"
      >
        Aucun contenu disponible pour ce chant.
        <template v-if="authStore.canManageChants">
          <NuxtLink :to="`/songbook/${id}/edit`" class="ml-1 text-(--color-primary-600) underline">
            Ajouter le contenu
          </NuxtLink>
        </template>
      </div>
    </div>

    <!-- Lecteur YouTube intégré (Teleport to body) -->
    <YoutubePlayerModal
      v-if="showYoutubePlayer && selectedChant?.youtube_url"
      :youtubeUrl="selectedChant.youtube_url"
      @close="showYoutubePlayer = false"
    />
  </div>
</template>
