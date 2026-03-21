<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import type { ChantRead, ChantCategorieRead } from '../types/chant'

const props = defineProps<{
  chants: ChantRead[]
  categories: ChantCategorieRead[]
  selectedId?: string
  isLoading?: boolean
}>()

const emit = defineEmits<{
  select: [id: string]
  search: [q: string]
  filterCategorie: [code: string]
}>()

const searchQuery = ref('')
const selectedCategorie = ref('')

watch(searchQuery, (v) => emit('search', v))
watch(selectedCategorie, (v) => emit('filterCategorie', v))

// Groupement des chants par artiste (artiste null → groupe "Inconnu")
const chantsByArtiste = computed(() => {
  const groups = new Map<string, ChantRead[]>()
  for (const chant of props.chants) {
    const key = chant.artiste ?? '—'
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(chant)
  }
  // NULLS LAST : '—' en dernier
  return [...groups.entries()].sort(([a], [b]) => {
    if (a === '—') return 1
    if (b === '—') return -1
    return a.localeCompare(b)
  })
})

function getCategorieByCode(code?: string): ChantCategorieRead | undefined {
  if (!code) return undefined
  return props.categories.find((c) => c.code === code)
}
</script>

<template>
  <div class="flex h-full flex-col gap-3">
    <!-- Barre de recherche -->
    <div class="relative">
      <Search class="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-(--color-neutral-400)" />
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher un chant…"
        class="w-full rounded-lg border border-(--color-neutral-200) py-2 pr-3 pl-9 text-sm focus:border-(--color-primary-400) focus:outline-none"
      />
    </div>

    <!-- Filtre catégorie -->
    <select
      v-model="selectedCategorie"
      class="w-full rounded-lg border border-(--color-neutral-200) px-3 py-2 text-sm focus:border-(--color-primary-400) focus:outline-none"
    >
      <option value="">Toutes les catégories</option>
      <option v-for="cat in categories" :key="cat.code" :value="cat.code">
        {{ cat.libelle }}
      </option>
    </select>

    <!-- Liste groupée par artiste -->
    <div
      v-if="isLoading"
      class="flex flex-1 items-center justify-center text-sm text-(--color-neutral-400)"
    >
      Chargement…
    </div>

    <div
      v-else-if="chants.length === 0"
      class="flex flex-1 items-center justify-center text-sm text-(--color-neutral-400)"
    >
      Aucun chant trouvé
    </div>

    <div v-else class="flex-1 space-y-4 overflow-y-auto">
      <div v-for="[artiste, group] in chantsByArtiste" :key="artiste">
        <p
          class="mb-1 px-1 text-xs font-semibold tracking-wide text-(--color-neutral-500) uppercase"
        >
          {{ artiste }}
        </p>
        <div class="space-y-1">
          <ChantCard
            v-for="chant in group"
            :key="chant.id"
            :chant="chant"
            :categorie="getCategorieByCode(chant.categorie_code)"
            :selected="chant.id === selectedId"
            @select="emit('select', $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
