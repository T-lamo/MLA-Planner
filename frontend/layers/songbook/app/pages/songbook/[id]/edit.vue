<script setup lang="ts">
import { ArrowLeft, ChevronRight, Trash2 } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { useUIStore } from '~~/layers/base/app/stores/useUiStore'
import type { ChantContenuCreate, ChantContenuRead } from '../../../types/chant'

const route = useRoute()
const uiStore = useUIStore()
const campusId = computed(() => uiStore.selectedCampusId ?? '')

const id = computed<string>(() => {
  const raw = route.params.id
  if (Array.isArray(raw)) return raw[0] ?? ''
  return raw ?? ''
})

definePageMeta({
  middleware: [
    function () {
      const auth = useAuthStore()
      if (!auth.canManageChants) return navigateTo('/songbook', { replace: true })
    },
  ],
})

const {
  categories,
  chants,
  selectedChant,
  isLoading,
  loadCategories,
  loadChants,
  selectChant,
  updateChant,
  deleteChant,
  upsertContenu,
  updateContenu,
} = useSongbook()

const artistesSuggestions = computed(() => {
  const all = chants.value.map((c) => c.artiste).filter((a): a is string => !!a)
  return [...new Set(all)].sort()
})

// ── Formulaire ────────────────────────────────────────────────────────────
const form = reactive({
  titre: '',
  artiste: '',
  categorie_code: '',
  youtube_url: '',
  tonalite: '',
  paroles_chords: '',
})

const isSaving = ref(false)
const titleError = ref('')

// ── Preview live (debounce 400ms) ─────────────────────────────────────────
const previewTonalite = ref('')
const previewContent = ref('')
let previewTimer: ReturnType<typeof setTimeout> | null = null

// Pré-remplissage quand le chant est chargé
watch(
  selectedChant,
  (chant) => {
    if (!chant) return
    form.titre = chant.titre
    form.artiste = chant.artiste ?? ''
    form.categorie_code = chant.categorie_code ?? ''
    form.youtube_url = chant.youtube_url ?? ''
    form.tonalite = chant.contenu?.tonalite ?? ''
    form.paroles_chords = chant.contenu?.paroles_chords ?? ''
    // Sync preview immédiat
    previewTonalite.value = form.tonalite
    previewContent.value = form.paroles_chords
  },
  { immediate: true },
)

// Détection des modifications non sauvegardées
const isDirty = computed(
  () =>
    form.titre !== (selectedChant.value?.titre ?? '') ||
    form.artiste !== (selectedChant.value?.artiste ?? '') ||
    form.categorie_code !== (selectedChant.value?.categorie_code ?? '') ||
    form.youtube_url !== (selectedChant.value?.youtube_url ?? '') ||
    form.paroles_chords !== (selectedChant.value?.contenu?.paroles_chords ?? '') ||
    form.tonalite !== (selectedChant.value?.contenu?.tonalite ?? ''),
)

function schedulePreview() {
  if (previewTimer) clearTimeout(previewTimer)
  previewTimer = setTimeout(() => {
    previewTonalite.value = form.tonalite
    previewContent.value = form.paroles_chords
  }, 400)
}

watch(() => form.tonalite, schedulePreview)
watch(() => form.paroles_chords, schedulePreview)

const previewContenu = computed<ChantContenuRead>(() => ({
  id: '',
  chant_id: '',
  tonalite: previewTonalite.value,
  paroles_chords: previewContent.value,
  version: 1,
  date_modification: new Date().toISOString(),
}))

// ── Sauvegarde ────────────────────────────────────────────────────────────
async function handleSave(contenu: ChantContenuCreate) {
  titleError.value = ''
  if (!form.titre.trim()) {
    titleError.value = 'Le titre est requis'
    return
  }
  isSaving.value = true
  await updateChant(id.value, {
    titre: form.titre.trim(),
    artiste: form.artiste.trim() || undefined,
    categorie_code: form.categorie_code || undefined,
    youtube_url: form.youtube_url.trim() || undefined,
  })
  const existing = selectedChant.value?.contenu
  if (existing) {
    await updateContenu(id.value, {
      tonalite: contenu.tonalite,
      paroles_chords: contenu.paroles_chords,
      version: existing.version,
    })
  } else {
    await upsertContenu(id.value, {
      tonalite: contenu.tonalite,
      paroles_chords: contenu.paroles_chords,
    })
  }
  isSaving.value = false
  await navigateTo(`/songbook/${id.value}`)
}

function handleCancel() {
  if (isDirty.value && !confirm('Des modifications non sauvegardées seront perdues. Continuer ?'))
    return
  navigateTo(`/songbook/${id.value}`)
}

async function handleDelete() {
  if (
    !selectedChant.value ||
    !confirm(`Supprimer définitivement « ${selectedChant.value.titre} » ?`)
  )
    return
  await deleteChant(id.value, campusId.value)
  await navigateTo('/songbook')
}

onMounted(async () => {
  if (categories.value.length === 0) await loadCategories()
  if (chants.value.length === 0) await loadChants(campusId.value)
  await selectChant(id.value)
})
</script>

<template>
  <div class="flex h-[calc(100vh-4rem)] flex-col overflow-hidden">
    <!-- ── Header ─────────────────────────────────────────────────────── -->
    <div
      class="flex items-center justify-between border-b border-(--color-neutral-200) bg-white px-6 py-4"
    >
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 text-sm text-(--color-neutral-500) hover:text-(--color-neutral-700)"
          @click="handleCancel"
        >
          <ArrowLeft class="h-4 w-4" />
          Répertoire
        </button>
        <ChevronRight class="h-3.5 w-3.5 shrink-0 text-(--color-neutral-300)" />
        <span class="max-w-[200px] truncate text-sm text-(--color-neutral-500)">
          {{ selectedChant?.titre ?? '…' }}
        </span>
        <ChevronRight class="h-3.5 w-3.5 shrink-0 text-(--color-neutral-300)" />
        <h1 class="text-base font-semibold text-(--color-neutral-900)">Modifier</h1>
      </div>
      <button
        v-if="selectedChant"
        type="button"
        class="inline-flex items-center gap-1.5 rounded-lg border border-(--color-red-200) px-3 py-1.5 text-sm text-(--color-red-600) hover:bg-(--color-red-50)"
        @click="handleDelete"
      >
        <Trash2 class="h-4 w-4" />
        Supprimer
      </button>
    </div>

    <!-- ── Corps (skeleton) ───────────────────────────────────────────── -->
    <div v-if="isLoading && !selectedChant" class="flex flex-1 items-center justify-center">
      <div class="w-full max-w-lg space-y-4 px-6">
        <div class="h-10 animate-pulse rounded-lg bg-(--color-neutral-100)" />
        <div class="h-8 w-1/2 animate-pulse rounded-lg bg-(--color-neutral-100)" />
        <div class="h-64 animate-pulse rounded-2xl bg-(--color-neutral-100)" />
      </div>
    </div>

    <!-- ── Corps (formulaire + preview) ──────────────────────────────── -->
    <div v-else class="flex flex-1 overflow-hidden">
      <!-- Formulaire -->
      <div class="flex-1 overflow-y-auto px-6 py-6">
        <div class="mx-auto max-w-2xl space-y-6">
          <!-- Métadonnées -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div class="sm:col-span-2">
              <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
                Titre <span class="text-(--color-red-500)">*</span>
              </label>
              <input
                v-model="form.titre"
                type="text"
                placeholder="Titre du chant"
                class="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none"
                :class="
                  titleError
                    ? 'border-(--color-red-400) focus:border-(--color-red-400)'
                    : 'border-(--color-neutral-300) focus:border-(--color-primary-400)'
                "
              />
              <p v-if="titleError" class="mt-1 text-xs text-(--color-red-500)">{{ titleError }}</p>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
                Artiste / Groupe
              </label>
              <input
                v-model="form.artiste"
                type="text"
                list="artistes-list"
                placeholder="Ex : Hillsong, ICC Worship…"
                class="w-full rounded-lg border border-(--color-neutral-300) px-3 py-2 text-sm focus:border-(--color-primary-400) focus:outline-none"
              />
              <datalist id="artistes-list">
                <option v-for="a in artistesSuggestions" :key="a" :value="a" />
              </datalist>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
                Catégorie
              </label>
              <ChantCategorieSelect v-model="form.categorie_code" :categories="categories" />
            </div>
            <div class="sm:col-span-2">
              <label class="mb-1 block text-sm font-medium text-(--color-neutral-700)">
                Lien YouTube
              </label>
              <input
                v-model="form.youtube_url"
                type="url"
                placeholder="https://www.youtube.com/watch?v=…"
                class="w-full rounded-lg border border-(--color-neutral-300) px-3 py-2 text-sm focus:border-(--color-primary-400) focus:outline-none"
              />
            </div>
          </div>

          <!-- Éditeur ChordPro -->
          <div class="rounded-2xl border border-(--color-neutral-200) bg-white p-5">
            <p class="mb-4 text-sm font-medium text-(--color-neutral-700)">Contenu ChordPro</p>
            <ChordProEditor
              v-model="form.paroles_chords"
              :tonalite="form.tonalite"
              :isSaving="isSaving"
              @update:tonalite="(v) => (form.tonalite = v)"
              @save="handleSave"
            />
          </div>
        </div>
      </div>

      <!-- Preview live (desktop) -->
      <div
        class="hidden w-96 shrink-0 overflow-y-auto border-l border-(--color-neutral-200) bg-(--color-neutral-50) lg:block"
      >
        <div
          class="sticky top-0 border-b border-(--color-neutral-200) bg-(--color-neutral-50) px-5 py-3"
        >
          <p class="text-xs font-semibold tracking-wide text-(--color-neutral-500) uppercase">
            Prévisualisation
          </p>
        </div>
        <div class="p-5">
          <div
            v-if="previewContent"
            class="rounded-xl border border-(--color-neutral-200) bg-white p-5"
          >
            <ChantContenuViewer :contenu="previewContenu" />
          </div>
          <div
            v-else
            class="flex h-40 items-center justify-center rounded-xl border border-(--color-neutral-200) bg-white text-sm text-(--color-neutral-400)"
          >
            Écrivez du contenu ChordPro pour voir l'aperçu
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
