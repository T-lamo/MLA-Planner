<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { CalendarOff, Plus, Trash2, AlertCircle, CheckCircle2 } from 'lucide-vue-next'
import AppSelect from '../../components/ui/AppSelect.vue'
import AppDrawer from '../../components/AppDrawer.vue'
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
const isDrawerOpen = ref(false)
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

function openDrawer() {
  resetForm()
  isDrawerOpen.value = true
}

async function handleSubmit() {
  if (!form.value.date_debut || !form.value.date_fin) return
  isSubmitting.value = true
  try {
    await store.declare({ ...form.value })
    isDrawerOpen.value = false
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

const isFormValid = computed(
  () =>
    !!form.value.date_debut &&
    !!form.value.date_fin &&
    form.value.date_fin >= form.value.date_debut,
)

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
  <div class="mx-auto flex w-full max-w-3xl flex-col gap-6 p-4 md:p-8">
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
      <button class="btn btn-primary" @click="openDrawer">
        <Plus class="size-4" />
        Déclarer
      </button>
    </div>

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
      <button class="btn btn-primary mt-1" @click="openDrawer">Déclarer une indisponibilité</button>
    </div>

    <!-- Liste -->
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

    <!-- Drawer de création -->
    <AppDrawer
      :isOpen="isDrawerOpen"
      title="Déclarer une indisponibilité"
      initialSize="standard"
      @close="isDrawerOpen = false"
    >
      <div class="flex flex-col gap-5">
        <p class="text-sm text-slate-500">
          Indiquez la période durant laquelle vous ne serez pas disponible.
        </p>

        <!-- Période -->
        <div class="grid grid-cols-2 gap-3">
          <div class="field">
            <label class="field-label">Date de début <span class="text-red-500">*</span></label>
            <input v-model="form.date_debut" type="date" required class="form-input" />
          </div>
          <div class="field">
            <label class="field-label">Date de fin <span class="text-red-500">*</span></label>
            <input
              v-model="form.date_fin"
              type="date"
              required
              :min="form.date_debut || undefined"
              class="form-input"
            />
          </div>
        </div>

        <!-- Ministère -->
        <AppSelect
          v-model="form.ministere_id"
          label="Ministère"
          :options="[
            { label: 'Global / Tous les ministères', value: null },
            ...myMinisteres.map((m) => ({ label: m.nom, value: m.id })),
          ]"
        />

        <!-- Motif -->
        <div class="field">
          <label class="field-label">
            Motif <span class="font-normal text-slate-400">(optionnel)</span>
          </label>
          <textarea
            v-model="form.motif"
            rows="3"
            placeholder="Vacances, maladie, déplacement..."
            class="form-input resize-none"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex gap-3">
          <button class="btn btn-secondary flex-1" @click="isDrawerOpen = false">Annuler</button>
          <button
            :disabled="!isFormValid || isSubmitting"
            class="btn btn-primary flex-1"
            @click="handleSubmit"
          >
            {{ isSubmitting ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </div>
      </template>
    </AppDrawer>
  </div>
</template>

<style scoped>
@reference "../../assets/css/main.css";

.indisp-card {
  @apply flex items-start gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm transition-all;
}

.badge {
  @apply inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap;
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

.list-enter-active,
.list-leave-active {
  transition: all 0.25s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
