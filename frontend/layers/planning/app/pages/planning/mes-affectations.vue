<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Bell, CheckCircle2, XCircle, Clock, MapPin, CalendarDays, Users } from 'lucide-vue-next'
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
type StatusConfig = { label: string; dot: string; badge: string }
const STATUS_CONFIG: Record<AffectationStatus, StatusConfig> = {
  PROPOSE: {
    label: 'En attente',
    dot: 'bg-amber-400',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  CONFIRME: {
    label: 'Confirmé',
    dot: 'bg-emerald-400',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  REFUSE: {
    label: 'Refusé',
    dot: 'bg-rose-400',
    badge: 'bg-rose-50 text-rose-700 border-rose-200',
  },
  PRESENT: {
    label: 'Présent',
    dot: 'bg-blue-400',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
  },
  ABSENT: {
    label: 'Absent',
    dot: 'bg-slate-300',
    badge: 'bg-slate-50 text-slate-500 border-slate-200',
  },
  RETARD: {
    label: 'En retard',
    dot: 'bg-orange-400',
    badge: 'bg-orange-50 text-orange-700 border-orange-200',
  },
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

function initials(name?: string) {
  if (!name) return '?'
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-8 p-4 md:p-8">
    <!-- En-tête -->
    <div class="flex items-center justify-between">
      <div>
        <div class="flex items-center gap-2.5">
          <div
            class="flex size-9 items-center justify-center rounded-xl"
            style="background-color: var(--color-primary-50)"
          >
            <Bell class="size-5" style="color: var(--color-primary-600)" />
          </div>
          <h1 class="text-xl font-bold text-slate-900">Mes affectations</h1>
        </div>
        <p class="mt-1 pl-11 text-sm text-slate-500">Répondez aux propositions d'affectation.</p>
      </div>

      <!-- Badge total -->
      <div
        v-if="pending.length > 0"
        class="flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-sm font-semibold text-amber-700"
      >
        <span class="size-2 animate-pulse rounded-full bg-amber-400"></span>
        {{ pending.length }} en attente
      </div>
    </div>

    <!-- Squelette -->
    <div v-if="store.loading" class="flex flex-col gap-3">
      <div v-for="n in 4" :key="n" class="h-24 animate-pulse rounded-2xl bg-slate-100"></div>
    </div>

    <template v-else>
      <!-- ── En attente ── -->
      <section v-if="pending.length > 0">
        <h2
          class="mb-3 flex items-center gap-2 text-xs font-bold tracking-wider text-amber-600 uppercase"
        >
          <span class="size-2 rounded-full bg-amber-400"></span>
          En attente de réponse ({{ pending.length }})
        </h2>
        <ul class="flex flex-col gap-3">
          <li
            v-for="aff in pending"
            :key="aff.id"
            class="overflow-hidden rounded-2xl border border-amber-100 bg-white shadow-sm transition-shadow hover:shadow-md"
          >
            <!-- Bande couleur gauche -->
            <div class="flex">
              <div class="w-1 shrink-0 rounded-l-2xl bg-amber-400"></div>
              <div class="flex flex-1 flex-col gap-3 p-4">
                <!-- Ligne 1 : type + ministère -->
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <p class="font-bold text-slate-900">{{ aff.activite_type ?? 'Activité' }}</p>
                    <p
                      v-if="aff.ministere_nom"
                      class="mt-0.5 flex items-center gap-1 text-xs text-slate-400"
                    >
                      <Users class="size-3" />
                      {{ aff.ministere_nom }}
                    </p>
                  </div>
                  <span
                    class="shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-semibold"
                    :class="STATUS_CONFIG['PROPOSE'].badge"
                  >
                    <span class="mr-1 inline-block size-1.5 rounded-full bg-amber-400"></span>
                    En attente
                  </span>
                </div>

                <!-- Ligne 2 : date + créneau -->
                <div class="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                  <span class="flex items-center gap-1">
                    <CalendarDays class="size-3.5 shrink-0" />
                    {{ formatDate(aff.slot_debut) }}
                  </span>
                  <span class="flex items-center gap-1">
                    <Clock class="size-3.5 shrink-0" />
                    {{ formatTime(aff.slot_debut) }}
                  </span>
                  <span
                    v-if="aff.slot_nom"
                    class="rounded-md bg-slate-100 px-2 py-0.5 font-medium text-slate-600"
                  >
                    {{ aff.slot_nom }}
                  </span>
                </div>

                <!-- Ligne 3 : lieu -->
                <div v-if="aff.lieu" class="flex items-center gap-1 text-xs text-slate-400">
                  <MapPin class="size-3 shrink-0" />
                  {{ aff.lieu }}
                </div>

                <!-- Actions -->
                <div class="flex gap-2 pt-1">
                  <button
                    class="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-rose-200 bg-white py-2 text-xs font-semibold text-rose-600 transition-colors hover:bg-rose-50 active:scale-95"
                    @click="store.refuseAffectation(aff.id)"
                  >
                    <XCircle class="size-4" />
                    Refuser
                  </button>
                  <button
                    class="flex flex-1 items-center justify-center gap-1.5 rounded-xl py-2 text-xs font-semibold text-white transition-all active:scale-95"
                    style="background-color: var(--color-primary-600)"
                    @click="store.acceptAffectation(aff.id)"
                  >
                    <CheckCircle2 class="size-4" />
                    Accepter
                  </button>
                </div>
              </div>
            </div>
          </li>
        </ul>
      </section>

      <!-- ── Confirmées ── -->
      <section v-if="confirmed.length > 0">
        <h2
          class="mb-3 flex items-center gap-2 text-xs font-bold tracking-wider text-emerald-600 uppercase"
        >
          <span class="size-2 rounded-full bg-emerald-400"></span>
          Confirmées ({{ confirmed.length }})
        </h2>
        <ul class="flex flex-col gap-2">
          <li
            v-for="aff in confirmed"
            :key="aff.id"
            class="flex items-center gap-3 rounded-xl border border-slate-100 bg-white p-3.5 shadow-sm"
          >
            <!-- Avatar initiales -->
            <div
              class="flex size-9 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-xs font-bold text-emerald-600"
            >
              {{ initials(aff.activite_type) }}
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold text-slate-800">
                {{ aff.activite_type ?? 'Activité' }}
              </p>
              <p class="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
                <CalendarDays class="size-3 shrink-0" />
                {{ formatDate(aff.slot_debut) }} · {{ formatTime(aff.slot_debut) }}
              </p>
            </div>
            <span
              class="shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-semibold"
              :class="STATUS_CONFIG['CONFIRME'].badge"
            >
              Confirmé
            </span>
          </li>
        </ul>
      </section>

      <!-- ── Historique ── -->
      <section v-if="others.length > 0">
        <h2
          class="mb-3 flex items-center gap-2 text-xs font-bold tracking-wider text-slate-400 uppercase"
        >
          <span class="size-2 rounded-full bg-slate-300"></span>
          Historique ({{ others.length }})
        </h2>
        <ul class="flex flex-col gap-2">
          <li
            v-for="aff in others"
            :key="aff.id"
            class="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3.5"
          >
            <div
              class="flex size-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-xs font-bold text-slate-400"
            >
              {{ initials(aff.activite_type) }}
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-slate-600">
                {{ aff.activite_type ?? 'Activité' }}
              </p>
              <p class="mt-0.5 flex items-center gap-1 text-xs text-slate-400">
                <CalendarDays class="size-3 shrink-0" />
                {{ formatDate(aff.slot_debut) }}
              </p>
            </div>
            <span
              class="shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-semibold"
              :class="STATUS_CONFIG[aff.statut_affectation_code as AffectationStatus].badge"
            >
              {{ STATUS_CONFIG[aff.statut_affectation_code as AffectationStatus].label }}
            </span>
          </li>
        </ul>
      </section>

      <!-- ── Vide ── -->
      <div
        v-if="store.affectations.length === 0"
        class="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-slate-200 py-16 text-center"
      >
        <div class="flex size-14 items-center justify-center rounded-2xl bg-slate-50">
          <Bell class="size-7 text-slate-300" />
        </div>
        <div>
          <p class="font-semibold text-slate-700">Aucune affectation</p>
          <p class="mt-1 text-sm text-slate-400">
            Vous serez notifié quand un responsable vous propose un créneau.
          </p>
        </div>
      </div>
    </template>
  </div>
</template>
