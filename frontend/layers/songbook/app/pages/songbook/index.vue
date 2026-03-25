<script setup lang="ts">
import { Library, Music, Plus, Clock } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

const authStore = useAuthStore()

const { categories, chants, isLoading, loadCategories, loadChants } = useSongbook()

// Palettes cycliques — valeurs JS car calculées par index (style inline autorisé)
const PALETTES = [
  { bg: '#eff6ff', border: '#bfdbfe', icon: '#1d4ed8', iconBg: '#dbeafe' },
  { bg: '#ecfdf5', border: '#a7f3d0', icon: '#047857', iconBg: '#d1fae5' },
  { bg: '#fffbeb', border: '#fde68a', icon: '#92400e', iconBg: '#fef3c7' },
  { bg: '#f5f3ff', border: '#ddd6fe', icon: '#5b21b6', iconBg: '#ede9fe' },
  { bg: '#fff1f2', border: '#fecdd3', icon: '#9f1239', iconBg: '#ffe4e6' },
]

function palette(index: number) {
  return PALETTES[index % PALETTES.length]!
}

// Nombre de chants par catégorie (calculé côté front)
const chantsByCategorie = computed(() => {
  const map = new Map<string, number>()
  for (const c of chants.value) {
    if (c.categorie_code) {
      map.set(c.categorie_code, (map.get(c.categorie_code) ?? 0) + 1)
    }
  }
  return map
})

// 6 derniers chants ajoutés
const recentChants = computed(() =>
  [...chants.value]
    .sort((a, b) => new Date(b.date_creation).getTime() - new Date(a.date_creation).getTime())
    .slice(0, 6),
)

onMounted(() => Promise.all([loadCategories(), loadChants()]))
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-10 px-4 py-8">
    <!-- ── En-tête ────────────────────────────────────────────────────── -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-(--color-neutral-900)">Répertoire de chants</h1>
        <p class="mt-1 text-sm text-(--color-neutral-500)">
          {{ chants.length }} chant{{ chants.length > 1 ? 's' : '' }} disponible{{
            chants.length > 1 ? 's' : ''
          }}
        </p>
      </div>
      <NuxtLink
        v-if="authStore.canManageChants"
        to="/songbook/new"
        class="inline-flex items-center gap-2 rounded-lg bg-(--color-primary-600) px-4 py-2 text-sm font-medium text-white hover:bg-(--color-primary-700)"
      >
        <Plus class="h-4 w-4" />
        Nouveau chant
      </NuxtLink>
    </div>

    <!-- ── État chargement ───────────────────────────────────────────── -->
    <div v-if="isLoading" class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
      <div
        v-for="n in 5"
        :key="n"
        class="h-36 animate-pulse rounded-2xl bg-(--color-neutral-100)"
      />
    </div>

    <!-- ── État vide ─────────────────────────────────────────────────── -->
    <div
      v-else-if="chants.length === 0 && !isLoading"
      class="flex flex-col items-center gap-4 py-20 text-center"
    >
      <div class="flex h-20 w-20 items-center justify-center rounded-full bg-(--color-neutral-100)">
        <Music class="h-10 w-10 text-(--color-neutral-400)" />
      </div>
      <p class="text-lg font-medium text-(--color-neutral-700)">Aucun chant dans le répertoire</p>
      <p class="text-sm text-(--color-neutral-400)">Commencez par ajouter vos premiers chants.</p>
      <NuxtLink
        v-if="authStore.canManageChants"
        to="/songbook/new"
        class="inline-flex items-center gap-2 rounded-lg bg-(--color-primary-600) px-4 py-2 text-sm font-medium text-white hover:bg-(--color-primary-700)"
      >
        <Plus class="h-4 w-4" />
        Ajouter un chant
      </NuxtLink>
    </div>

    <!-- ── Grille des catégories ─────────────────────────────────────── -->
    <div v-else class="space-y-10">
      <div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        <!-- Card "Tous les chants" -->
        <NuxtLink
          to="/songbook/browse"
          class="group flex flex-col gap-3 rounded-2xl border border-(--color-neutral-200) bg-white p-5 transition-all duration-200 hover:scale-[1.02] hover:border-(--color-neutral-300)"
        >
          <div
            class="flex h-11 w-11 items-center justify-center rounded-xl bg-(--color-neutral-100)"
          >
            <Library class="h-5 w-5 text-(--color-neutral-600)" />
          </div>
          <div>
            <p class="font-semibold text-(--color-neutral-900)">Tous les chants</p>
            <p class="mt-0.5 text-sm text-(--color-neutral-500)">
              {{ chants.length }} chant{{ chants.length > 1 ? 's' : '' }}
            </p>
          </div>
        </NuxtLink>

        <!-- Cards par catégorie -->
        <NuxtLink
          v-for="(cat, index) in categories"
          :key="cat.code"
          :to="`/songbook/browse?categorie=${cat.code}`"
          class="group flex flex-col gap-3 rounded-2xl border p-5 transition-all duration-200 hover:scale-[1.02]"
          :style="{
            backgroundColor: palette(index).bg,
            borderColor: palette(index).border,
          }"
        >
          <div
            class="flex h-11 w-11 items-center justify-center rounded-xl"
            :style="{ backgroundColor: palette(index).iconBg }"
          >
            <Music class="h-5 w-5" :style="{ color: palette(index).icon }" />
          </div>
          <div>
            <p class="font-semibold text-(--color-neutral-900)">{{ cat.libelle }}</p>
            <p class="mt-0.5 text-sm text-(--color-neutral-600)">
              {{ chantsByCategorie.get(cat.code) ?? 0 }}
              chant{{ (chantsByCategorie.get(cat.code) ?? 0) > 1 ? 's' : '' }}
            </p>
          </div>
        </NuxtLink>
      </div>

      <!-- ── Récemment ajoutés ──────────────────────────────────────── -->
      <section v-if="recentChants.length > 0">
        <div class="mb-4 flex items-center gap-2">
          <Clock class="h-4 w-4 text-(--color-neutral-400)" />
          <h2 class="text-sm font-semibold tracking-wide text-(--color-neutral-500) uppercase">
            Récemment ajoutés
          </h2>
        </div>
        <div class="flex gap-3 overflow-x-auto pb-2">
          <NuxtLink
            v-for="chant in recentChants"
            :key="chant.id"
            :to="`/songbook/${chant.id}`"
            class="flex min-w-[160px] shrink-0 flex-col gap-1.5 rounded-xl border border-(--color-neutral-200) bg-white p-4 transition-all duration-150 hover:border-(--color-primary-300) hover:bg-(--color-primary-50)"
          >
            <div
              class="flex h-8 w-8 items-center justify-center rounded-lg bg-(--color-primary-50)"
            >
              <Music class="h-4 w-4 text-(--color-primary-600)" />
            </div>
            <p class="line-clamp-2 text-sm font-medium text-(--color-neutral-900)">
              {{ chant.titre }}
            </p>
            <p v-if="chant.artiste" class="truncate text-xs text-(--color-neutral-400)">
              {{ chant.artiste }}
            </p>
          </NuxtLink>
        </div>
      </section>
    </div>
  </div>
</template>
