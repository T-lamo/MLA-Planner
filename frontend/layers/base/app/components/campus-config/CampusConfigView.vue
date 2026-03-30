<template>
  <div class="space-y-6">
    <!-- Sélecteur de campus -->
    <div class="flex flex-wrap items-center gap-3">
      <!-- Pills si ≤ 4 campus, sinon select -->
      <div v-if="campuses.length <= 4 && campuses.length > 0" class="flex flex-wrap gap-2">
        <button
          v-for="campus in campuses"
          :key="campus.id"
          type="button"
          :class="[
            'rounded-full border px-4 py-1.5 text-sm font-medium transition-colors',
            selectedCampusId === campus.id
              ? 'border-(--color-primary-500) bg-(--color-primary-600) text-white'
              : 'border-slate-200 bg-white text-slate-700 hover:border-(--color-primary-300) hover:text-(--color-primary-700)',
          ]"
          @click="selectCampus(campus.id)"
        >
          {{ campus.nom }}
        </button>
      </div>

      <div v-else-if="campuses.length > 4" class="form-select-wrapper">
        <select
          :value="selectedCampusId"
          class="form-input form-select"
          @change="(e) => selectCampus((e.target as HTMLSelectElement).value)"
        >
          <option v-for="campus in campuses" :key="campus.id" :value="campus.id">
            {{ campus.nom }}
          </option>
        </select>
        <svg
          class="form-select-chevron"
          viewBox="0 0 14 14"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M3 5l4 4 4-4" />
        </svg>
      </div>

      <!-- Bouton Init Statuts (uniquement si non initialisés) -->
      <button
        v-if="summary && summary.statuts_planning.length === 0"
        type="button"
        class="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700 transition-colors hover:bg-amber-100"
        :disabled="isInitialisingStatuts"
        @click="handleInitStatuts"
      >
        <Loader2 v-if="isInitialisingStatuts" class="size-4 animate-spin" />
        <RefreshCw v-else class="size-4" />
        Init Statuts
      </button>

      <!-- Bouton Configuration initiale -->
      <button
        v-if="selectedCampusId"
        type="button"
        class="ml-auto flex items-center gap-2 rounded-lg border border-(--color-primary-200) bg-(--color-primary-50) px-3 py-2 text-sm font-medium text-(--color-primary-700) transition-colors hover:bg-(--color-primary-100)"
        @click="
          setup.open(
            ministeres,
            allCatalogByCategory.flatMap((item) => item.roles),
          )
        "
      >
        <Zap class="size-4" />
        Configuration initiale
      </button>
    </div>

    <CampusConfigSetupDrawer />

    <!-- Skeleton de chargement -->
    <div v-if="isLoading" class="space-y-3">
      <div v-for="n in 3" :key="n" class="h-14 animate-pulse rounded-xl bg-slate-100" />
    </div>

    <!-- Contenu chargé -->
    <template v-else-if="selectedCampusId">
      <!-- Liste des ministères -->
      <ul v-if="ministeres.length > 0" class="space-y-3">
        <CampusConfigMinistereAccordion
          v-for="min in ministeres"
          :key="min.id"
          :ministere="min"
          :isOpen="openMinisteres.has(min.id)"
          @toggle="toggleMinistere(min.id)"
          @remove="handleRemoveMinistere"
          @edit="handleEditMinistere"
        />
      </ul>

      <!-- État vide -->
      <div
        v-else
        class="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 py-16 text-center"
      >
        <Building2 class="mb-3 size-10 text-slate-300" />
        <p class="font-medium text-slate-500">Aucun ministère configuré</p>
        <p class="mt-1 text-sm text-slate-400">
          Ajoutez un ministère pour commencer la configuration
        </p>
      </div>

      <!-- Bouton + Ministère -->
      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-(--color-primary-200) py-3 text-sm font-medium text-(--color-primary-600) transition-colors hover:border-(--color-primary-400) hover:bg-(--color-primary-50)"
        @click="form.openAddMinistere()"
      >
        <Plus class="size-4" />
        Ajouter un ministère
      </button>
    </template>

    <!-- Aucun campus -->
    <div v-else class="rounded-xl bg-slate-50 py-12 text-center">
      <p class="text-slate-400">Aucun campus disponible</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Building2, Loader2, Plus, RefreshCw, Zap } from 'lucide-vue-next'
import { useCampusConfig } from '../../composables/useCampusConfig'
import { useCampusConfigForm } from '../../composables/useCampusConfigForm'
import { useCampusSetup } from '../../composables/useCampusSetup'

const {
  campuses,
  selectedCampusId,
  summary,
  allCatalogByCategory,
  isLoading,
  ministeres,
  selectCampus,
  removeMinistere,
  initStatuts,
} = useCampusConfig()

const form = useCampusConfigForm()
const { openEditMinistere } = form
const setup = useCampusSetup()

const openMinisteres = ref(new Set<string>())
const isInitialisingStatuts = ref(false)

function toggleMinistere(id: string): void {
  if (openMinisteres.value.has(id)) {
    openMinisteres.value.delete(id)
  } else {
    openMinisteres.value.add(id)
  }
}

async function handleRemoveMinistere(ministereId: string): Promise<void> {
  try {
    await removeMinistere(ministereId)
    openMinisteres.value.delete(ministereId)
  } catch {
    // Erreur déjà notifiée par l'intercepteur
  }
}

async function handleInitStatuts(): Promise<void> {
  isInitialisingStatuts.value = true
  try {
    await initStatuts()
  } catch {
    // Erreur déjà notifiée par l'intercepteur
  } finally {
    isInitialisingStatuts.value = false
  }
}

function handleEditMinistere(ministereId: string): void {
  const min = ministeres.value.find((m) => m.id === ministereId)
  if (!min) return
  openEditMinistere(ministereId, min.nom, min.description)
}
</script>
