<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { CalendarOff, Plus, Trash2, X, AlertCircle, CheckCircle2 } from 'lucide-vue-next'
import { useIndisponibiliteStore } from '../../stores/useIndisponibiliteStore'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import type { IndisponibiliteCreate } from '~~/layers/base/types/indisponibilites'
import type { MinistereSimple } from '~~/layers/base/types/ministere'
import { ProfileRepository } from '../../repositories/ProfileRepository'

const authStore = useAuthStore()
const store = useIndisponibiliteStore()

// Ministères du membre courant
const myMinisteres = ref<MinistereSimple[]>([])

onMounted(async () => {
  await store.fetchMine()
  try {
    const profile = await new ProfileRepository().getMyProfile()
    myMinisteres.value = profile.ministeres ?? []
  } catch {
    // ignore
  }
})

// ----- Formulaire -----
const isFormOpen = ref(false)
const isSubmitting = ref(false)

function getDefaultDates() {
  const today = new Date()
  const threeMonthsLater = new Date(today)
  threeMonthsLater.setMonth(threeMonthsLater.getMonth() + 3)
  const toISO = (d: Date) => d.toISOString().slice(0, 10)
  return { date_debut: toISO(today), date_fin: toISO(threeMonthsLater) }
}

const form = ref<IndisponibiliteCreate>({
  ...getDefaultDates(),
  motif: '',
  ministere_id: null,
  membre_id: authStore.currentUser?.membreId ?? '',
})

function resetForm() {
  form.value = {
    ...getDefaultDates(),
    motif: '',
    ministere_id: null,
    membre_id: authStore.currentUser?.membreId ?? '',
  }
}

function openForm() {
  resetForm()
  isFormOpen.value = true
}

function closeForm() {
  isFormOpen.value = false
}

async function handleSubmit() {
  if (!form.value.date_debut || !form.value.date_fin) return
  isSubmitting.value = true
  try {
    await store.declare({ ...form.value })
    isFormOpen.value = false
    resetForm()
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete(id: string) {
  await store.remove(id)
}

// ----- Tri : futures d'abord, puis passées -----
const sorted = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return [...store.myIndisponibilites].sort((a, b) => {
    const aFuture = (a.date_fin ?? '') >= today
    const bFuture = (b.date_fin ?? '') >= today
    if (aFuture && !bFuture) return -1
    if (!aFuture && bFuture) return 1
    return (a.date_debut ?? '').localeCompare(b.date_debut ?? '')
  })
})

// ----- Helpers -----
function formatDate(d: string | null) {
  if (!d) return '—'
  const [y = '', m = '', day = ''] = d.split('-')
  const months = [
    'jan',
    'fév',
    'mar',
    'avr',
    'mai',
    'juin',
    'jul',
    'aoû',
    'sep',
    'oct',
    'nov',
    'déc',
  ]
  return `${parseInt(day, 10)} ${months[parseInt(m, 10) - 1]}. ${y}`
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 md:p-8">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="flex size-10 items-center justify-center rounded-xl bg-amber-50">
          <CalendarOff class="size-5 text-amber-600" />
        </div>
        <div>
          <h1 class="text-xl font-bold text-slate-900">Mes indisponibilités</h1>
          <p class="text-sm text-slate-500">Déclarez vos périodes d'indisponibilité</p>
        </div>
      </div>
      <button class="btn-primary flex items-center gap-2" @click="openForm">
        <Plus class="size-4" />
        Déclarer
      </button>
    </div>

    <!-- Layout 2 colonnes sur desktop -->
    <div class="flex flex-col gap-6 lg:flex-row lg:items-start">
      <!-- Liste -->
      <div class="flex-1 space-y-3">
        <!-- Skeleton -->
        <template v-if="store.loading">
          <div v-for="n in 3" :key="n" class="h-20 animate-pulse rounded-xl bg-slate-100" />
        </template>

        <!-- Vide -->
        <div
          v-else-if="sorted.length === 0"
          class="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-200 py-12 text-slate-400"
        >
          <CalendarOff class="size-10 opacity-40" />
          <p class="text-sm">Aucune indisponibilité déclarée</p>
        </div>

        <!-- Items -->
        <TransitionGroup v-else name="list" tag="div" class="space-y-3">
          <div v-for="item in sorted" :key="item.id" class="indisp-card group">
            <div class="flex flex-1 flex-col gap-1">
              <!-- Badge statut -->
              <div class="flex items-center gap-2">
                <span :class="['badge', item.validee ? 'badge-green' : 'badge-amber']">
                  <component :is="item.validee ? CheckCircle2 : AlertCircle" class="size-3" />
                  {{ item.validee ? 'Validée' : 'En attente' }}
                </span>
                <span v-if="item.ministere_libelle" class="text-xs text-slate-500">
                  · {{ item.ministere_libelle }}
                </span>
                <span v-else class="text-xs text-slate-400">· Global</span>
              </div>

              <!-- Dates -->
              <p class="text-sm font-medium text-slate-800">
                {{ formatDate(item.date_debut) }}
                &rarr;
                {{ formatDate(item.date_fin) }}
              </p>

              <!-- Motif -->
              <p v-if="item.motif" class="line-clamp-1 text-xs text-slate-500">
                {{ item.motif }}
              </p>
            </div>

            <!-- Supprimer -->
            <button
              v-if="!item.validee"
              class="ml-auto shrink-0 rounded-lg p-1.5 text-slate-400 opacity-0 transition-all group-hover:opacity-100 hover:bg-red-50 hover:text-red-500"
              title="Supprimer"
              @click="handleDelete(item.id)"
            >
              <Trash2 class="size-4" />
            </button>
            <span
              v-else
              class="ml-auto shrink-0 rounded-lg p-1.5 text-slate-300"
              title="Impossible de supprimer une indisponibilité validée"
            >
              <Trash2 class="size-4" />
            </span>
          </div>
        </TransitionGroup>
      </div>

      <!-- Formulaire (panel latéral desktop / drawer mobile) -->
      <Transition name="slide-right">
        <aside v-if="isFormOpen" class="indisp-form-panel">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-slate-800">Nouvelle indisponibilité</h2>
            <button class="rounded-lg p-1 text-slate-400 hover:text-slate-700" @click="closeForm">
              <X class="size-4" />
            </button>
          </div>

          <form class="mt-4 flex flex-col gap-4" @submit.prevent="handleSubmit">
            <!-- Date début -->
            <div class="field">
              <label class="field-label">Date de début *</label>
              <input v-model="form.date_debut" type="date" required class="field-input" />
            </div>

            <!-- Date fin -->
            <div class="field">
              <label class="field-label">Date de fin *</label>
              <input
                v-model="form.date_fin"
                type="date"
                required
                :min="form.date_debut || undefined"
                class="field-input"
              />
            </div>

            <!-- Ministère -->
            <div class="field">
              <label class="field-label">Ministère</label>
              <select v-model="form.ministere_id" class="field-input">
                <option :value="null">Global / Tous les ministères</option>
                <option v-for="m in myMinisteres" :key="m.id" :value="m.id">
                  {{ m.nom }}
                </option>
              </select>
            </div>

            <!-- Motif -->
            <div class="field">
              <label class="field-label">Motif (optionnel)</label>
              <textarea
                v-model="form.motif"
                rows="3"
                placeholder="Raison de l'indisponibilité..."
                class="field-input resize-none"
              />
            </div>

            <button
              type="submit"
              :disabled="isSubmitting"
              class="btn-primary w-full justify-center disabled:opacity-60"
            >
              <span v-if="isSubmitting">Enregistrement…</span>
              <span v-else>Enregistrer</span>
            </button>
          </form>
        </aside>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
@reference "../../assets/css/main.css";

.indisp-card {
  @apply flex items-start gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm transition-all;
}

.indisp-form-panel {
  @apply w-full rounded-2xl border border-slate-100 bg-white p-5 shadow-sm lg:w-80 lg:shrink-0;
}

.badge {
  @apply inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold;
}

.badge-green {
  @apply bg-emerald-50 text-emerald-700;
}

.badge-amber {
  @apply bg-amber-50 text-amber-700;
}

.field {
  @apply flex flex-col gap-1;
}

.field-label {
  @apply text-xs font-medium text-slate-600;
}

.field-input {
  @apply rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 transition-all outline-none focus:border-(--color-primary-400) focus:bg-white focus:ring-2 focus:ring-(--color-primary-100);
}

.btn-primary {
  @apply flex items-center gap-2 rounded-xl bg-(--color-primary-600) px-4 py-2 font-semibold text-white shadow-sm transition-all hover:bg-(--color-primary-700) active:scale-95;
}

/* Transitions liste */
.list-enter-active,
.list-leave-active {
  transition: all 0.25s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

/* Formulaire latéral slide */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.25s ease;
}
.slide-right-enter-from,
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
