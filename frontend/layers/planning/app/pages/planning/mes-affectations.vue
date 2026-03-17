<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Bell, CheckCircle2, XCircle, Clock } from 'lucide-vue-next'
import { useMyAffectationsStore } from '../../stores/useMyAffectationsStore'
import type { AffectationStatus } from '../../types/planning.types'

definePageMeta({ layout: 'default' })

const store = useMyAffectationsStore()

onMounted(() => store.fetchMyAffectations())

// --- GROUPES ---
const pending = computed(() =>
  store.affectations.filter((a) => a.statut_affectation_code === 'PROPOSE'),
)
const confirmed = computed(() =>
  store.affectations.filter((a) => a.statut_affectation_code === 'CONFIRME'),
)
const others = computed(() =>
  store.affectations.filter((a) =>
    ['REFUSE', 'PRESENT', 'ABSENT', 'RETARD'].includes(a.statut_affectation_code),
  ),
)

// --- HELPERS ---
const STATUS_CONFIG: Record<AffectationStatus, { label: string; class: string }> = {
  PROPOSE: { label: 'En attente', class: 'bg-amber-100 text-amber-700' },
  CONFIRME: { label: 'Confirmé', class: 'bg-emerald-100 text-emerald-700' },
  REFUSE: { label: 'Refusé', class: 'bg-rose-100 text-rose-700' },
  PRESENT: { label: 'Présent', class: 'bg-blue-100 text-blue-700' },
  ABSENT: { label: 'Absent', class: 'bg-slate-100 text-slate-500' },
  RETARD: { label: 'En retard', class: 'bg-orange-100 text-orange-700' },
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
</script>

<template>
  <div class="mx-auto flex w-full max-w-4xl flex-col gap-6 p-4 md:p-8">
    <!-- En-tête -->
    <div class="flex flex-col gap-1">
      <div class="flex items-center gap-2">
        <Bell class="text-primary-600 size-5" />
        <h1 class="text-xl font-bold text-slate-800">Mes affectations</h1>
      </div>
      <p class="text-sm text-slate-500">Acceptez ou refusez les propositions d'affectation.</p>
    </div>

    <!-- Squelette -->
    <div v-if="store.loading" class="flex flex-col gap-3">
      <div v-for="n in 4" :key="n" class="h-20 animate-pulse rounded-xl bg-slate-100"></div>
    </div>

    <template v-else>
      <!-- En attente -->
      <section v-if="pending.length > 0">
        <h2 class="mb-3 text-xs font-bold tracking-wider text-amber-600 uppercase">
          En attente de réponse ({{ pending.length }})
        </h2>
        <ul class="flex flex-col gap-2">
          <li
            v-for="aff in pending"
            :key="aff.id"
            class="flex items-center justify-between gap-4 rounded-xl border border-amber-100 bg-amber-50 p-4"
          >
            <div class="min-w-0 flex-1">
              <p class="truncate font-semibold text-slate-800">
                {{ aff.activite_type ?? 'Activité' }}
              </p>
              <p class="mt-0.5 text-xs text-slate-500">
                {{ aff.slot_nom }} · {{ formatDate(aff.slot_debut) }}
              </p>
              <p v-if="aff.ministere_nom" class="mt-0.5 text-xs text-slate-400">
                {{ aff.ministere_nom }}
              </p>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <button
                class="flex items-center gap-1 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-semibold text-rose-600 transition-colors hover:bg-rose-50"
                @click="store.refuseAffectation(aff.id)"
              >
                <XCircle class="size-3.5" />
                Refuser
              </button>
              <button
                class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-semibold text-white transition-all active:scale-95"
                style="background-color: var(--color-primary-600)"
                @click="store.acceptAffectation(aff.id)"
              >
                <CheckCircle2 class="size-3.5" />
                Accepter
              </button>
            </div>
          </li>
        </ul>
      </section>

      <!-- Confirmées -->
      <section v-if="confirmed.length > 0">
        <h2 class="mb-3 text-xs font-bold tracking-wider text-emerald-600 uppercase">
          Confirmées ({{ confirmed.length }})
        </h2>
        <ul class="flex flex-col gap-2">
          <li
            v-for="aff in confirmed"
            :key="aff.id"
            class="flex items-center gap-4 rounded-xl border border-slate-100 bg-white p-4"
          >
            <CheckCircle2 class="size-5 shrink-0 text-emerald-500" />
            <div class="min-w-0 flex-1">
              <p class="truncate font-semibold text-slate-800">
                {{ aff.activite_type ?? 'Activité' }}
              </p>
              <p class="mt-0.5 text-xs text-slate-500">
                {{ aff.slot_nom }} · {{ formatDate(aff.slot_debut) }}
              </p>
            </div>
            <span
              class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
              :class="STATUS_CONFIG['CONFIRME'].class"
            >
              {{ STATUS_CONFIG['CONFIRME'].label }}
            </span>
          </li>
        </ul>
      </section>

      <!-- Autres statuts -->
      <section v-if="others.length > 0">
        <h2 class="mb-3 text-xs font-bold tracking-wider text-slate-400 uppercase">
          Historique ({{ others.length }})
        </h2>
        <ul class="flex flex-col gap-2">
          <li
            v-for="aff in others"
            :key="aff.id"
            class="flex items-center gap-4 rounded-xl border border-slate-100 bg-white p-4"
          >
            <Clock class="size-5 shrink-0 text-slate-400" />
            <div class="min-w-0 flex-1">
              <p class="truncate font-semibold text-slate-700">
                {{ aff.activite_type ?? 'Activité' }}
              </p>
              <p class="mt-0.5 text-xs text-slate-500">
                {{ aff.slot_nom }} · {{ formatDate(aff.slot_debut) }}
              </p>
            </div>
            <span
              class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
              :class="STATUS_CONFIG[aff.statut_affectation_code as AffectationStatus].class"
            >
              {{ STATUS_CONFIG[aff.statut_affectation_code as AffectationStatus].label }}
            </span>
          </li>
        </ul>
      </section>

      <!-- Vide -->
      <div
        v-if="store.affectations.length === 0"
        class="rounded-xl border border-slate-100 bg-slate-50 p-10 text-center text-sm text-slate-400"
      >
        Aucune affectation pour le moment.
      </div>
    </template>
  </div>
</template>
