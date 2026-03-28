<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { refDebounced } from '@vueuse/core'
import { Search, X, GripVertical, Music, ChevronUp, ChevronDown, Trash2 } from 'lucide-vue-next'
import { ChantRepository } from '~~/layers/songbook/app/repositories/ChantRepository'
import type { ChantRead } from '~~/layers/songbook/app/types/chant'
import type { UseRepertoireReturn } from '../composables/useRepertoire'

interface Props {
  campusId: string
  repertoire: UseRepertoireReturn
}

const props = defineProps<Props>()

const chantRepo = new ChantRepository()

// ── Recherche ─────────────────────────────────────────────────────────────
const searchRaw = ref('')
const searchQuery = refDebounced(searchRaw, 300)
const searchResults = ref<ChantRead[]>([])
const isSearching = ref(false)
const showDropdown = ref(false)

const addedIds = computed(() => new Set(props.repertoire.chants.value.map((c) => c.id)))

async function runSearch(q: string) {
  if (!q.trim()) {
    searchResults.value = []
    showDropdown.value = false
    return
  }
  isSearching.value = true
  try {
    const result = await chantRepo.listChants({
      campus_id: props.campusId,
      q: q.trim(),
      limit: 10,
    })
    searchResults.value = result.data
    showDropdown.value = result.data.length > 0
  } catch {
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

// Watch debounced query
watch(searchQuery, runSearch)

function selectChant(chant: ChantRead) {
  props.repertoire.addChant({
    id: chant.id,
    titre: chant.titre,
    artiste: chant.artiste ?? undefined,
    youtube_url: chant.youtube_url ?? undefined,
    categorie_code: chant.categorie_code ?? undefined,
    ordre: props.repertoire.chants.value.length,
  })
  searchRaw.value = ''
  searchResults.value = []
  showDropdown.value = false
}

function onSearchBlur() {
  window.setTimeout(() => {
    showDropdown.value = false
  }, 150)
}

function clearSearch() {
  searchRaw.value = ''
  searchResults.value = []
  showDropdown.value = false
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <!-- Recherche chant -->
    <div class="relative">
      <div class="relative flex items-center">
        <Search class="pointer-events-none absolute left-3 size-4 text-slate-400" />
        <input
          v-model="searchRaw"
          type="text"
          placeholder="Rechercher un chant par titre ou artiste…"
          class="form-input w-full bg-white pr-8 pl-9"
          autocomplete="off"
          @focus="searchQuery && runSearch(searchQuery)"
          @blur="onSearchBlur"
        />
        <button
          v-if="searchRaw"
          type="button"
          class="absolute right-2.5 rounded p-0.5 text-slate-400 hover:text-slate-700"
          @click="clearSearch"
        >
          <X class="size-3.5" />
        </button>
      </div>

      <!-- Dropdown résultats -->
      <Transition name="dropdown-fade">
        <div
          v-if="showDropdown"
          class="absolute z-10 mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg"
        >
          <div v-if="isSearching" class="flex items-center gap-2 px-4 py-3 text-sm text-slate-400">
            <span
              class="inline-block size-4 animate-spin rounded-full border-2 border-slate-200 border-t-slate-500"
            />
            Recherche…
          </div>
          <template v-else>
            <button
              v-for="chant in searchResults"
              :key="chant.id"
              type="button"
              class="flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-slate-50 disabled:opacity-40"
              :disabled="addedIds.has(chant.id)"
              @click="selectChant(chant)"
            >
              <Music class="size-4 shrink-0 text-slate-400" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium text-slate-800">{{ chant.titre }}</p>
                <p v-if="chant.artiste" class="truncate text-xs text-slate-400">
                  {{ chant.artiste }}
                </p>
              </div>
              <span
                v-if="addedIds.has(chant.id)"
                class="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-400"
              >
                Déjà ajouté
              </span>
            </button>
          </template>
        </div>
      </Transition>
    </div>

    <!-- Liste ordonnée -->
    <div v-if="!repertoire.isEmpty.value" class="flex flex-col gap-1.5">
      <TransitionGroup name="chant-list">
        <div
          v-for="(chant, index) in repertoire.chants.value"
          :key="chant.id"
          class="group flex items-center gap-2 rounded-xl border border-slate-100 bg-white px-3 py-2 shadow-xs transition-shadow hover:shadow-sm"
        >
          <!-- Drag handle (visuel) -->
          <GripVertical
            class="size-4 shrink-0 cursor-grab text-slate-300 group-hover:text-slate-400"
          />

          <!-- Numéro -->
          <span class="w-5 shrink-0 text-center text-xs font-bold text-slate-300">
            {{ index + 1 }}
          </span>

          <!-- Infos -->
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold text-slate-800">{{ chant.titre }}</p>
            <p v-if="chant.artiste" class="truncate text-xs text-slate-400">{{ chant.artiste }}</p>
          </div>

          <!-- Youtube badge -->
          <span
            v-if="chant.youtube_url"
            class="shrink-0 rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-500"
          >
            YT
          </span>

          <!-- Actions ordre -->
          <div class="flex shrink-0 items-center gap-0.5">
            <button
              type="button"
              class="rounded p-1 text-slate-300 transition-colors hover:bg-slate-100 hover:text-slate-600 disabled:opacity-0"
              :disabled="index === 0"
              @click="repertoire.moveUp(index)"
            >
              <ChevronUp class="size-3.5" />
            </button>
            <button
              type="button"
              class="rounded p-1 text-slate-300 transition-colors hover:bg-slate-100 hover:text-slate-600 disabled:opacity-0"
              :disabled="index === repertoire.chants.value.length - 1"
              @click="repertoire.moveDown(index)"
            >
              <ChevronDown class="size-3.5" />
            </button>
            <button
              type="button"
              class="rounded p-1 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-500"
              @click="repertoire.removeChant(chant.id)"
            >
              <Trash2 class="size-3.5" />
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- État vide -->
    <div
      v-else
      class="flex items-center gap-3 rounded-xl border border-dashed border-slate-200 px-4 py-5 text-sm text-slate-400"
    >
      <Music class="size-5 shrink-0 text-slate-300" />
      <span>Aucun chant — utilisez la recherche ci-dessus pour composer le répertoire.</span>
    </div>
  </div>
</template>

<style scoped>
@reference "~~/layers/base/app/assets/css/main.css";

.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.chant-list-enter-active,
.chant-list-leave-active {
  transition: all 0.2s ease;
}
.chant-list-enter-from,
.chant-list-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}
.chant-list-move {
  transition: transform 0.2s ease;
}
</style>
