<template>
  <header
    class="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-8"
  >
    <div class="flex items-center gap-2 md:gap-6">
      <button
        class="flex rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden"
        aria-label="Ouvrir le menu"
        @click="ui.toggleSidebar"
      >
        <Menu class="size-6" />
      </button>

      <CampusSelector />

      <nav
        v-if="breadcrumb.section"
        class="hidden items-center text-sm text-slate-500 lg:flex"
        aria-label="Breadcrumb"
      >
        <span>{{ breadcrumb.section }}</span>
        <template v-if="breadcrumb.page">
          <ChevronRight class="mx-2 size-4" />
          <span class="font-semibold text-slate-900">{{ breadcrumb.page }}</span>
        </template>
      </nav>
    </div>

    <div class="flex items-center gap-2 md:gap-4">
      <button class="btn-primary flex items-center justify-center gap-2 px-3 py-2 md:px-4">
        <Plus class="size-5 md:size-4" />
        <span class="hidden md:inline">Créer Planning</span>
      </button>

      <NuxtLink
        to="/planning/mes-affectations"
        class="relative rounded-full p-2 text-slate-500 hover:bg-slate-50"
        aria-label="Mes affectations en attente"
      >
        <Bell class="size-5" />
        <span
          v-if="pendingCount > 0"
          class="absolute top-0.5 right-0.5 flex size-4 items-center justify-center rounded-full border border-white bg-red-500 text-[9px] font-bold text-white"
          >{{ pendingCount > 9 ? '9+' : pendingCount }}</span
        >
      </NuxtLink>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { ChevronRight, Plus, Menu, Bell } from 'lucide-vue-next'
import { useUIStore } from '../stores/useUiStore'
import { useMyAffectationsStore } from '~~/layers/planning/app/stores/useMyAffectationsStore'

const ui = useUIStore()
const myAffectationsStore = useMyAffectationsStore()
const route = useRoute()

const pendingCount = computed(() => myAffectationsStore.pendingCount)

// Initialisation au montage du parent pour garantir la disponibilité des données
onMounted(async () => {
  try {
    await ui.initializeUI()
    await myAffectationsStore.refreshPendingCount()
  } catch {
    // silently ignore init errors
  }
})

const SECTION_LABELS: Record<string, string> = {
  planning: 'Planning',
  songbook: 'Répertoire',
  admin: 'Administration',
}

const PAGE_LABELS: Record<string, string> = {
  calendar: 'Calendrier',
  list: 'Liste',
  'mes-affectations': 'Mes affectations',
  browse: 'Tous les chants',
  new: 'Nouveau chant',
  categories: 'Catégories',
  edit: 'Modifier',
  profiles: 'Profils',
  campuses: 'Campus',
  'campus-config': 'Config campus',
  super: 'Super admin',
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

const breadcrumb = computed(() => {
  const segments = route.path.split('/').filter(Boolean)
  const section = segments[0] ?? ''
  const sectionLabel = SECTION_LABELS[section] ?? ''

  const rest = segments.slice(1)
  const namedSegment = [...rest].reverse().find((s) => !UUID_RE.test(s))

  let page = ''
  if (namedSegment) {
    page = PAGE_LABELS[namedSegment] ?? namedSegment
  } else if (rest.some((s) => UUID_RE.test(s))) {
    page = 'Détail'
  }

  return { section: sectionLabel, page }
})
</script>

<style scoped>
@reference "../assets/css/main.css";

.btn-primary {
  @apply rounded-lg bg-(--color-primary-600) font-semibold text-white shadow-sm transition-all hover:bg-(--color-primary-700) active:scale-95;
}
</style>
