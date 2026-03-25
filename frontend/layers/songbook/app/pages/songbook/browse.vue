<script setup lang="ts">
import { Search, Plus, ChevronDown, SlidersHorizontal } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import type { ChantRead, ChantCategorieRead } from '../../types/chant'

const authStore = useAuthStore()

const { categories, chants, isLoading, loadCategories, loadChants } = useSongbook()

const route = useRoute()
const router = useRouter()

// ── État des filtres (initialisé depuis l'URL) ─────────────────────────────
const selectedCategorie = ref((route.query.categorie as string) ?? '')
const selectedArtiste = ref((route.query.artiste as string) ?? '')
const rawSearch = ref((route.query.q as string) ?? '')
const searchQuery = ref(rawSearch.value)
const sortBy = ref<'date' | 'titre' | 'artiste'>('date')
const visibleCount = ref(20)
const showMobileFilters = ref(false)

// ── Debounce recherche 300ms ───────────────────────────────────────────────
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(rawSearch, (v) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    searchQuery.value = v
    visibleCount.value = 20
  }, 300)
})

// ── Sync URL ←→ état filtres ───────────────────────────────────────────────
watch([selectedCategorie, selectedArtiste, searchQuery], () => {
  const q: Record<string, string> = {}
  if (selectedCategorie.value) q.categorie = selectedCategorie.value
  if (selectedArtiste.value) q.artiste = selectedArtiste.value
  if (searchQuery.value) q.q = searchQuery.value
  router.replace({ query: q })
  visibleCount.value = 20
})

// ── Artistes uniques calculés depuis les chants chargés ───────────────────
const artisteOptions = computed<string[]>(() => {
  const set = new Set<string>()
  for (const c of chants.value) {
    if (c.artiste) set.add(c.artiste)
  }
  return [...set].sort((a, b) => a.localeCompare(b))
})

// ── Filtre + tri + pagination ──────────────────────────────────────────────
const filteredChants = computed<ChantRead[]>(() => {
  const q = searchQuery.value.toLowerCase()
  return chants.value.filter((c) => {
    if (selectedCategorie.value && c.categorie_code !== selectedCategorie.value) return false
    if (selectedArtiste.value && c.artiste !== selectedArtiste.value) return false
    if (q && !c.titre.toLowerCase().includes(q) && !c.artiste?.toLowerCase().includes(q))
      return false
    return true
  })
})

const sortedChants = computed<ChantRead[]>(() => {
  const arr = [...filteredChants.value]
  if (sortBy.value === 'titre') return arr.sort((a, b) => a.titre.localeCompare(b.titre))
  if (sortBy.value === 'artiste')
    return arr.sort((a, b) => (a.artiste ?? '').localeCompare(b.artiste ?? ''))
  return arr.sort(
    (a, b) => new Date(b.date_creation).getTime() - new Date(a.date_creation).getTime(),
  )
})

const visibleChants = computed<ChantRead[]>(() => sortedChants.value.slice(0, visibleCount.value))
const hasMore = computed(() => visibleCount.value < sortedChants.value.length)

function loadMore() {
  visibleCount.value += 20
}

function getCategorieByCode(code?: string): ChantCategorieRead | undefined {
  if (!code) return undefined
  return categories.value.find((c) => c.code === code)
}

// ── Titre dynamique de la zone principale ─────────────────────────────────
const mainTitle = computed(() => {
  const count = sortedChants.value.length
  const base = `${count} chant${count > 1 ? 's' : ''}`
  const parts: string[] = []
  if (selectedCategorie.value) {
    const cat = getCategorieByCode(selectedCategorie.value)
    if (cat) parts.push(cat.libelle)
  }
  if (selectedArtiste.value) parts.push(selectedArtiste.value)
  return parts.length ? `${base} — ${parts.join(' / ')}` : base
})

function clearFilters() {
  selectedCategorie.value = ''
  selectedArtiste.value = ''
  rawSearch.value = ''
  searchQuery.value = ''
}

onMounted(() => Promise.all([loadCategories(), loadChants()]))
</script>

<template>
  <div class="flex h-[calc(100vh-4rem)] overflow-hidden">
    <!-- ── Sidebar filtres (desktop) ──────────────────────────────────── -->
    <aside
      class="hidden w-64 shrink-0 flex-col gap-5 overflow-y-auto border-r border-(--color-neutral-200) bg-white p-5 md:flex"
    >
      <!-- Recherche -->
      <div class="relative">
        <Search
          class="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-(--color-neutral-400)"
        />
        <input
          v-model="rawSearch"
          type="text"
          placeholder="Rechercher…"
          class="w-full rounded-lg border border-(--color-neutral-200) py-2 pr-3 pl-9 text-sm focus:border-(--color-primary-400) focus:outline-none"
        />
      </div>

      <!-- Catégories -->
      <div>
        <p class="mb-2 text-xs font-semibold tracking-wide text-(--color-neutral-500) uppercase">
          Catégories
        </p>
        <div class="flex flex-col gap-1">
          <button
            type="button"
            class="rounded-lg px-3 py-1.5 text-left text-sm transition-colors"
            :class="
              selectedCategorie === ''
                ? 'bg-(--color-primary-100) font-medium text-(--color-primary-700)'
                : 'text-(--color-neutral-700) hover:bg-(--color-neutral-100)'
            "
            @click="selectedCategorie = ''"
          >
            Tout
          </button>
          <button
            v-for="cat in categories"
            :key="cat.code"
            type="button"
            class="rounded-lg px-3 py-1.5 text-left text-sm transition-colors"
            :class="
              selectedCategorie === cat.code
                ? 'bg-(--color-primary-100) font-medium text-(--color-primary-700)'
                : 'text-(--color-neutral-700) hover:bg-(--color-neutral-100)'
            "
            @click="selectedCategorie = cat.code"
          >
            {{ cat.libelle }}
          </button>
        </div>
      </div>

      <!-- Artistes -->
      <div>
        <p class="mb-2 text-xs font-semibold tracking-wide text-(--color-neutral-500) uppercase">
          Artiste
        </p>
        <div class="relative">
          <select
            v-model="selectedArtiste"
            class="w-full appearance-none rounded-lg border border-(--color-neutral-200) py-2 pr-8 pl-3 text-sm focus:border-(--color-primary-400) focus:outline-none"
          >
            <option value="">Tous les artistes</option>
            <option v-for="a in artisteOptions" :key="a" :value="a">{{ a }}</option>
          </select>
          <ChevronDown
            class="pointer-events-none absolute top-1/2 right-2.5 h-4 w-4 -translate-y-1/2 text-(--color-neutral-400)"
          />
        </div>
      </div>

      <!-- Reset filtres -->
      <button
        v-if="selectedCategorie || selectedArtiste || searchQuery"
        type="button"
        class="text-sm text-(--color-neutral-500) underline underline-offset-2 hover:text-(--color-neutral-700)"
        @click="clearFilters"
      >
        Effacer les filtres
      </button>
    </aside>

    <!-- ── Zone principale ────────────────────────────────────────────── -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Header -->
      <div
        class="flex items-center justify-between border-b border-(--color-neutral-200) bg-white px-6 py-4"
      >
        <div class="flex items-center gap-3">
          <!-- Bouton filtres mobile -->
          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-lg border border-(--color-neutral-200) px-3 py-1.5 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50) md:hidden"
            @click="showMobileFilters = !showMobileFilters"
          >
            <SlidersHorizontal class="h-4 w-4" />
            Filtres
          </button>
          <h1 class="text-base font-semibold text-(--color-neutral-900)">{{ mainTitle }}</h1>
        </div>
        <div class="flex items-center gap-3">
          <!-- Tri -->
          <div class="relative hidden sm:block">
            <select
              v-model="sortBy"
              class="appearance-none rounded-lg border border-(--color-neutral-200) py-1.5 pr-7 pl-3 text-sm text-(--color-neutral-700) focus:border-(--color-primary-400) focus:outline-none"
            >
              <option value="date">Date</option>
              <option value="titre">Titre A→Z</option>
              <option value="artiste">Artiste A→Z</option>
            </select>
            <ChevronDown
              class="pointer-events-none absolute top-1/2 right-2 h-3.5 w-3.5 -translate-y-1/2 text-(--color-neutral-400)"
            />
          </div>
          <NuxtLink
            v-if="authStore.canManageChants"
            to="/songbook/new"
            class="inline-flex items-center gap-1.5 rounded-lg bg-(--color-primary-600) px-3 py-1.5 text-sm font-medium text-white hover:bg-(--color-primary-700)"
          >
            <Plus class="h-4 w-4" />
            <span class="hidden sm:inline">Nouveau</span>
          </NuxtLink>
        </div>
      </div>

      <!-- Filtres mobiles dépliables -->
      <Transition
        enterActiveClass="transition-all duration-200"
        enterFromClass="opacity-0 -translate-y-2"
        enterToClass="opacity-100 translate-y-0"
        leaveActiveClass="transition-all duration-150"
        leaveFromClass="opacity-100 translate-y-0"
        leaveToClass="opacity-0 -translate-y-2"
      >
        <div
          v-if="showMobileFilters"
          class="flex flex-wrap gap-2 border-b border-(--color-neutral-200) bg-white px-4 py-3 md:hidden"
        >
          <div class="relative w-full">
            <Search
              class="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-(--color-neutral-400)"
            />
            <input
              v-model="rawSearch"
              type="text"
              placeholder="Rechercher…"
              class="w-full rounded-lg border border-(--color-neutral-200) py-2 pr-3 pl-9 text-sm focus:outline-none"
            />
          </div>
          <button
            v-for="cat in [{ code: '', libelle: 'Tout' }, ...categories]"
            :key="cat.code"
            type="button"
            class="rounded-full border px-3 py-1 text-xs font-medium transition-colors"
            :class="
              selectedCategorie === cat.code
                ? 'border-(--color-primary-400) bg-(--color-primary-100) text-(--color-primary-700)'
                : 'border-(--color-neutral-200) text-(--color-neutral-600) hover:bg-(--color-neutral-50)'
            "
            @click="selectedCategorie = cat.code"
          >
            {{ cat.libelle }}
          </button>
        </div>
      </Transition>

      <!-- Liste des chants -->
      <div class="flex-1 overflow-y-auto px-6 py-6">
        <!-- Skeletons loading -->
        <div v-if="isLoading" class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="n in 6"
            :key="n"
            class="h-20 animate-pulse rounded-xl bg-(--color-neutral-100)"
          />
        </div>

        <!-- Vide -->
        <div
          v-else-if="sortedChants.length === 0"
          class="flex flex-col items-center gap-3 py-16 text-center"
        >
          <p class="text-sm font-medium text-(--color-neutral-700)">Aucun chant trouvé</p>
          <p class="text-xs text-(--color-neutral-400)">
            <template v-if="selectedCategorie || selectedArtiste || searchQuery">
              Essayez de modifier vos filtres.
              <button
                type="button"
                class="ml-1 text-(--color-primary-600) underline"
                @click="clearFilters"
              >
                Effacer
              </button>
            </template>
            <template v-else> Aucun chant n'a encore été ajouté. </template>
          </p>
        </div>

        <!-- Grille -->
        <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <ChantCard
            v-for="chant in visibleChants"
            :key="chant.id"
            :chant="chant"
            :categorie="getCategorieByCode(chant.categorie_code)"
            @select="navigateTo('/songbook/' + $event)"
          />
        </div>

        <!-- Load more -->
        <div v-if="hasMore" class="mt-6 flex justify-center">
          <button
            type="button"
            class="rounded-lg border border-(--color-neutral-200) px-5 py-2 text-sm text-(--color-neutral-700) hover:bg-(--color-neutral-50)"
            @click="loadMore"
          >
            Voir plus ({{ sortedChants.length - visibleCount }} restants)
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
