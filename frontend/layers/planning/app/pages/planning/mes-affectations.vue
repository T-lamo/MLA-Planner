<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Bell,
  CheckCircle2,
  XCircle,
  CalendarDays,
  Users,
  MapPin,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Clock,
} from 'lucide-vue-next'
import { useMyAffectationsStore } from '../../stores/useMyAffectationsStore'
import type { AffectationMemberRead, AffectationStatus } from '../../types/planning.types'
import AppTable from '~~/layers/base/app/components/ui/AppTable.vue'
import AppPagination from '~~/layers/base/app/components/ui/AppPagination.vue'

definePageMeta({ layout: 'default' })

const store = useMyAffectationsStore()

onMounted(() => store.fetchMyAffectations())

// ── Filtres ──────────────────────────────────────────────────────────────────
const selectedStatus = ref<AffectationStatus | 'TOUS'>('TOUS')
const filterDateDebut = ref('')
const filterDateFin = ref('')
const sortAsc = ref(true)

type StatusConfig = { label: string; chip: string; chipActive: string; badge: string }
const STATUS_CONFIG: Record<AffectationStatus, StatusConfig> = {
  PROPOSE: {
    label: 'En attente',
    chip: 'border-amber-200 text-amber-600 hover:bg-amber-50',
    chipActive: 'bg-amber-500 border-amber-500 text-white',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  CONFIRME: {
    label: 'Confirmé',
    chip: 'border-emerald-200 text-emerald-600 hover:bg-emerald-50',
    chipActive: 'bg-emerald-500 border-emerald-500 text-white',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  REFUSE: {
    label: 'Refusé',
    chip: 'border-rose-200 text-rose-600 hover:bg-rose-50',
    chipActive: 'bg-rose-500 border-rose-500 text-white',
    badge: 'bg-rose-50 text-rose-700 border-rose-200',
  },
  PRESENT: {
    label: 'Présent',
    chip: 'border-blue-200 text-blue-600 hover:bg-blue-50',
    chipActive: 'bg-blue-500 border-blue-500 text-white',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
  },
  ABSENT: {
    label: 'Absent',
    chip: 'border-slate-200 text-slate-500 hover:bg-slate-50',
    chipActive: 'bg-slate-400 border-slate-400 text-white',
    badge: 'bg-slate-50 text-slate-500 border-slate-200',
  },
  RETARD: {
    label: 'En retard',
    chip: 'border-orange-200 text-orange-600 hover:bg-orange-50',
    chipActive: 'bg-orange-500 border-orange-500 text-white',
    badge: 'bg-orange-50 text-orange-700 border-orange-200',
  },
}

const STATUS_ORDER: AffectationStatus[] = [
  'PROPOSE',
  'CONFIRME',
  'REFUSE',
  'PRESENT',
  'ABSENT',
  'RETARD',
]

// ── Liste filtrée + triée ─────────────────────────────────────────────────────
const pendingCount = computed(
  () => store.affectations.filter((a) => a.statut_affectation_code === 'PROPOSE').length,
)

const filtered = computed<AffectationMemberRead[]>(() => {
  let list = [...store.affectations]

  if (selectedStatus.value !== 'TOUS') {
    list = list.filter((a) => a.statut_affectation_code === selectedStatus.value)
  }

  if (filterDateDebut.value) {
    list = list.filter((a) => a.slot_debut.slice(0, 10) >= filterDateDebut.value)
  }

  if (filterDateFin.value) {
    list = list.filter((a) => a.slot_debut.slice(0, 10) <= filterDateFin.value)
  }

  list.sort((a, b) => {
    const diff = new Date(a.slot_debut).getTime() - new Date(b.slot_debut).getTime()
    return sortAsc.value ? diff : -diff
  })

  return list
})

const hasActiveFilter = computed(
  () => selectedStatus.value !== 'TOUS' || !!filterDateDebut.value || !!filterDateFin.value,
)

function resetFilters() {
  selectedStatus.value = 'TOUS'
  filterDateDebut.value = ''
  filterDateFin.value = ''
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatDateCompact(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  })
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

const affColumns = [
  { key: 'date', label: 'Date' },
  { key: 'activite_type', label: 'Activité' },
  { key: 'slot_nom', label: 'Créneau' },
  { key: 'ministere_nom', label: 'Ministère', width: 'hidden lg:table-cell' },
  { key: 'statut_affectation_code', label: 'Statut' },
  { key: 'actions', label: '' },
]
</script>

<template>
  <div class="mx-auto flex w-full max-w-4xl flex-col gap-4 p-4 md:p-6">
    <!-- ── En-tête ── -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <div class="bg-primary-50 flex size-8 items-center justify-center rounded-lg">
          <Bell class="text-primary-600 size-4" />
        </div>
        <div>
          <h1 class="text-lg font-bold text-slate-900">Mes affectations</h1>
          <p class="text-xs text-slate-400">{{ store.affectations.length }} au total</p>
        </div>
      </div>
      <div
        v-if="pendingCount > 0"
        class="flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700"
      >
        <span class="size-1.5 animate-pulse rounded-full bg-amber-400"></span>
        {{ pendingCount }} en attente
      </div>
    </div>

    <!-- ── Barre de filtres ── -->
    <div class="rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
      <!-- Chips statut -->
      <div
        class="mb-3 flex gap-1.5 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        <button
          class="shrink-0 rounded-full border px-3 py-1 text-xs font-medium transition-colors"
          :class="
            selectedStatus === 'TOUS'
              ? 'border-slate-700 bg-slate-700 text-white'
              : 'border-slate-200 text-slate-500 hover:bg-slate-50'
          "
          @click="selectedStatus = 'TOUS'"
        >
          Tous
        </button>
        <button
          v-for="s in STATUS_ORDER"
          :key="s"
          class="shrink-0 rounded-full border px-3 py-1 text-xs font-medium transition-colors"
          :class="selectedStatus === s ? STATUS_CONFIG[s].chipActive : STATUS_CONFIG[s].chip"
          @click="selectedStatus = selectedStatus === s ? 'TOUS' : s"
        >
          {{ STATUS_CONFIG[s].label }}
        </button>
      </div>

      <!-- Période + tri -->
      <div class="flex flex-wrap items-end gap-2">
        <!-- Du / Au : colonne sur mobile, ligne sur sm+ -->
        <div class="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
          <div class="flex items-center gap-1.5">
            <CalendarDays class="size-3.5 shrink-0 text-slate-400" />
            <span class="w-5 shrink-0 text-xs text-slate-500">Du</span>
            <input v-model="filterDateDebut" type="date" class="form-input form-input-sm w-36" />
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-5 shrink-0 text-xs text-slate-500">Au</span>
            <input
              v-model="filterDateFin"
              type="date"
              :min="filterDateDebut"
              class="form-input form-input-sm w-36"
            />
          </div>
        </div>

        <div class="ml-auto flex items-center gap-2">
          <!-- Reset -->
          <button
            v-if="hasActiveFilter"
            class="text-xs font-medium text-slate-400 hover:text-slate-600"
            @click="resetFilters"
          >
            Réinitialiser
          </button>

          <!-- Tri date -->
          <button class="btn btn-secondary btn-sm" @click="sortAsc = !sortAsc">
            <component :is="sortAsc ? ArrowUp : ArrowDown" class="size-3.5" />
            {{ sortAsc ? 'Plus proche' : 'Plus récent' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Squelette ── -->
    <div v-if="store.loading" class="space-y-1.5">
      <div v-for="n in 5" :key="n" class="h-12 animate-pulse rounded-xl bg-slate-100" />
    </div>

    <template v-else>
      <!-- ── Liste ── -->
      <div v-if="filtered.length > 0">
        <!-- Tableau desktop -->
        <div
          class="hidden overflow-hidden rounded-xl border border-slate-100 bg-white shadow-sm sm:block"
        >
          <AppTable
            :columns="affColumns"
            :rows="filtered as unknown as Record<string, unknown>[]"
            :loading="store.loading"
            emptyLabel="Aucune affectation"
          >
            <template #header-date>
              <button
                class="flex items-center gap-1 hover:text-slate-700"
                @click="sortAsc = !sortAsc"
              >
                Date
                <component :is="sortAsc ? ArrowUp : ArrowDown" class="size-3" />
              </button>
            </template>

            <template #cell-date="{ row }">
              <p class="font-medium whitespace-nowrap text-slate-800">
                {{ formatDateCompact((row as unknown as AffectationMemberRead).slot_debut) }}
              </p>
              <p class="flex items-center gap-1 text-xs text-slate-400">
                <Clock class="size-3 shrink-0" />
                {{ formatTime((row as unknown as AffectationMemberRead).slot_debut) }}
              </p>
            </template>

            <template #cell-activite_type="{ row }">
              <p class="font-semibold text-slate-800">
                {{ (row as unknown as AffectationMemberRead).activite_type ?? '—' }}
              </p>
              <p
                v-if="(row as unknown as AffectationMemberRead).lieu"
                class="flex items-center gap-1 text-xs text-slate-400"
              >
                <MapPin class="size-3 shrink-0" />
                {{ (row as unknown as AffectationMemberRead).lieu }}
              </p>
            </template>

            <template #cell-slot_nom="{ value }">
              <span class="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                {{ (value as string | null) || '—' }}
              </span>
            </template>

            <template #cell-ministere_nom="{ value }">
              <span v-if="value" class="flex items-center gap-1 text-xs text-slate-500">
                <Users class="size-3 shrink-0" />
                {{ value as string }}
              </span>
              <span v-else class="text-xs text-slate-300">—</span>
            </template>

            <template #cell-statut_affectation_code="{ value }">
              <span
                class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold"
                :class="STATUS_CONFIG[value as AffectationStatus].badge"
              >
                {{ STATUS_CONFIG[value as AffectationStatus].label }}
              </span>
            </template>

            <template #cell-actions="{ row }">
              <div
                v-if="
                  (row as unknown as AffectationMemberRead).statut_affectation_code === 'PROPOSE'
                "
                class="flex items-center gap-1.5"
              >
                <button
                  class="flex items-center gap-1 rounded-lg border border-rose-200 px-2.5 py-1.5 text-xs font-semibold text-rose-600 transition-colors hover:bg-rose-50"
                  @click="store.refuseAffectation((row as unknown as AffectationMemberRead).id)"
                >
                  <XCircle class="size-3.5" />
                  Refuser
                </button>
                <button
                  class="btn btn-primary btn-sm"
                  @click="store.acceptAffectation((row as unknown as AffectationMemberRead).id)"
                >
                  <CheckCircle2 class="size-3.5" />
                  Accepter
                </button>
              </div>
            </template>

            <template #pagination>
              <AppPagination
                :currentPage="store.currentPage"
                :totalPages="store.totalPages"
                :total="store.total"
                :loading="store.loading"
                @change="
                  (page) => {
                    store.goToPage(page)
                    store.fetchMyAffectations()
                  }
                "
              />
            </template>
          </AppTable>
        </div>

        <!-- Cartes mobile -->
        <ul class="flex flex-col gap-2 sm:hidden">
          <li
            v-for="aff in filtered"
            :key="aff.id"
            class="w-full overflow-hidden rounded-xl border bg-white shadow-sm"
            :class="
              aff.statut_affectation_code === 'PROPOSE' ? 'border-amber-100' : 'border-slate-100'
            "
          >
            <div class="flex min-w-0">
              <!-- Bande couleur -->
              <div
                class="w-0.5 shrink-0"
                :class="{
                  'bg-amber-400': aff.statut_affectation_code === 'PROPOSE',
                  'bg-emerald-400': aff.statut_affectation_code === 'CONFIRME',
                  'bg-rose-400': aff.statut_affectation_code === 'REFUSE',
                  'bg-blue-400': aff.statut_affectation_code === 'PRESENT',
                  'bg-slate-300': aff.statut_affectation_code === 'ABSENT',
                  'bg-orange-400': aff.statut_affectation_code === 'RETARD',
                }"
              ></div>

              <div class="flex min-w-0 flex-1 items-center gap-3 px-3 py-3">
                <!-- Date bloc -->
                <div class="w-16 shrink-0 text-center">
                  <p class="text-xs font-bold text-slate-800">
                    {{ formatDateCompact(aff.slot_debut).split(' ').slice(1).join(' ') }}
                  </p>
                  <p class="text-[10px] text-slate-400">{{ formatTime(aff.slot_debut) }}</p>
                </div>

                <!-- Info -->
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-semibold text-slate-800">
                    {{ aff.activite_type ?? 'Activité' }}
                  </p>
                  <p class="mt-0.5 flex items-center gap-1 text-xs text-slate-400">
                    <span class="truncate">{{ aff.slot_nom }}</span>
                    <span v-if="aff.ministere_nom" class="shrink-0">· {{ aff.ministere_nom }}</span>
                  </p>
                </div>

                <!-- Statut / Actions -->
                <div class="ml-auto shrink-0">
                  <!-- Actions pour PROPOSE -->
                  <div v-if="aff.statut_affectation_code === 'PROPOSE'" class="flex gap-1.5">
                    <button
                      class="rounded-lg border border-rose-200 p-1.5 text-rose-500 hover:bg-rose-50"
                      @click="store.refuseAffectation(aff.id)"
                    >
                      <XCircle class="size-4" />
                    </button>
                    <button
                      class="btn btn-primary btn-icon"
                      @click="store.acceptAffectation(aff.id)"
                    >
                      <CheckCircle2 class="size-4" />
                    </button>
                  </div>
                  <!-- Badge statut -->
                  <span
                    v-else
                    class="inline-block rounded-full border px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap"
                    :class="STATUS_CONFIG[aff.statut_affectation_code as AffectationStatus].badge"
                  >
                    {{ STATUS_CONFIG[aff.statut_affectation_code as AffectationStatus].label }}
                  </span>
                </div>
              </div>
            </div>
          </li>
        </ul>

        <!-- Compteur résultats filtrés -->
        <p v-if="hasActiveFilter" class="mt-2 text-center text-xs text-slate-400">
          {{ filtered.length }} résultat{{ filtered.length > 1 ? 's' : '' }} sur
          {{ store.affectations.length }}
        </p>
      </div>

      <!-- ── Aucun résultat (filtre actif) ── -->
      <div
        v-else-if="hasActiveFilter"
        class="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-200 py-10 text-center"
      >
        <ArrowUpDown class="size-8 text-slate-300" />
        <div>
          <p class="text-sm font-medium text-slate-600">Aucun résultat</p>
          <p class="mt-0.5 text-xs text-slate-400">
            Modifiez les filtres pour voir plus d'affectations.
          </p>
        </div>
        <button
          class="text-xs font-medium underline"
          style="color: var(--color-primary-600)"
          @click="resetFilters"
        >
          Réinitialiser les filtres
        </button>
      </div>

      <!-- ── Aucune affectation ── -->
      <div
        v-else
        class="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-slate-200 py-14 text-center"
      >
        <div class="flex size-12 items-center justify-center rounded-2xl bg-slate-50">
          <Bell class="size-6 text-slate-300" />
        </div>
        <div>
          <p class="font-semibold text-slate-700">Aucune affectation</p>
          <p class="mt-1 text-xs text-slate-400">
            Vous serez notifié quand un responsable vous propose un créneau.
          </p>
        </div>
      </div>
    </template>
  </div>
</template>
