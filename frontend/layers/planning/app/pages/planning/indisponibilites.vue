<script setup lang="ts">
import { ref, computed, reactive, watch, onMounted } from 'vue'
import {
  AlertCircle,
  CheckCircle2,
  Trash2,
  CheckCheck,
  Users,
  Plus,
  CalendarOff,
} from 'lucide-vue-next'
import AppDrawer from '~~/layers/base/app/components/AppDrawer.vue'
import { useIndisponibiliteStore } from '~~/layers/base/app/stores/useIndisponibiliteStore'
import { useUIStore } from '~~/layers/base/app/stores/useUiStore'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import type { MinistereSimple } from '~~/layers/base/types/ministere'
import { ProfileRepository } from '~~/layers/base/app/repositories/ProfileRepository'

const store = useIndisponibiliteStore()
const uiStore = useUIStore()
const authStore = useAuthStore()

const campusMinisteres = ref<MinistereSimple[]>([])
const drawerOpen = ref(false)
const todayDate = new Date().toISOString().slice(0, 10)

const newForm = reactive({
  date_debut: '',
  date_fin: '',
  motif: '',
  ministere_id: '',
})

function resetForm() {
  newForm.date_debut = ''
  newForm.date_fin = ''
  newForm.motif = ''
  newForm.ministere_id = ''
}

onMounted(async () => {
  try {
    const profile = await new ProfileRepository().getMyProfile()
    campusMinisteres.value = profile.ministeres ?? []
  } catch {
    // ignore
  }
  if (!authStore.hasAdminAccess) {
    store.fetchMine()
  }
})

// Charger à chaque changement de campus (admin seulement)
watch(
  () => uiStore.selectedCampusId,
  (id) => {
    if (id && authStore.hasAdminAccess) store.fetchByCampus(id)
  },
  { immediate: true },
)

async function applyFilters() {
  if (uiStore.selectedCampusId && authStore.hasAdminAccess) {
    await store.fetchByCampus(uiStore.selectedCampusId)
  }
}

async function handleValider(id: string) {
  await store.valider(id)
}

async function handleDelete(id: string) {
  await store.adminRemove(id)
}

async function handleDeleteMine(id: string) {
  await store.remove(id)
}

async function handleSubmit() {
  const memberId = authStore.user?.membreId
  if (!memberId || !newForm.date_debut || !newForm.date_fin) return
  await store.declare({
    membre_id: memberId,
    date_debut: newForm.date_debut,
    date_fin: newForm.date_fin,
    motif: newForm.motif || undefined,
    ministere_id: newForm.ministere_id || undefined,
  })
  drawerOpen.value = false
  resetForm()
}

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

const hasCampus = computed(() => !!uiStore.selectedCampusId)
const isFormValid = computed(
  () => newForm.date_debut && newForm.date_fin && newForm.date_fin >= newForm.date_debut,
)
</script>

<template>
  <div class="mx-auto flex w-full max-w-6xl flex-col gap-6 p-4 md:p-8">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="flex size-10 items-center justify-center rounded-xl bg-amber-50">
          <CalendarOff class="size-5 text-amber-600" />
        </div>
        <div>
          <h1 class="text-xl font-bold text-slate-900">Indisponibilités</h1>
          <p class="text-sm text-slate-500">
            {{
              authStore.hasAdminAccess
                ? 'Gérez les indisponibilités des membres'
                : 'Déclarez vos indisponibilités'
            }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <!-- Badge en attente (admin) -->
        <div
          v-if="authStore.hasAdminAccess && store.pendingCount > 0"
          class="flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 text-sm font-medium text-red-600"
        >
          <AlertCircle class="size-4" />
          {{ store.pendingCount }} en attente
        </div>

        <!-- Bouton déclarer -->
        <button
          class="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold text-white transition-all active:scale-95"
          style="background-color: var(--color-primary-600)"
          @click="drawerOpen = true"
        >
          <Plus class="size-4" />
          Déclarer
        </button>
      </div>
    </div>

    <!-- Section admin : filtres + liste -->
    <template v-if="authStore.hasAdminAccess">
      <!-- Barre de filtres -->
      <div
        class="flex flex-wrap items-end gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm"
      >
        <div class="field min-w-36">
          <label class="field-label">Ministère</label>
          <select v-model="store.filters.ministere_id" class="field-input" @change="applyFilters">
            <option value="">Tous</option>
            <option v-for="m in campusMinisteres" :key="m.id" :value="m.id">{{ m.nom }}</option>
          </select>
        </div>
        <div class="field min-w-36">
          <label class="field-label">Du</label>
          <input
            v-model="store.filters.date_debut"
            type="date"
            class="field-input"
            @change="applyFilters"
          />
        </div>
        <div class="field min-w-36">
          <label class="field-label">Au</label>
          <input
            v-model="store.filters.date_fin"
            type="date"
            class="field-input"
            @change="applyFilters"
          />
        </div>
        <label class="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
          <input
            v-model="store.filters.validee_only"
            type="checkbox"
            class="rounded"
            @change="applyFilters"
          />
          Non validées uniquement
        </label>
      </div>

      <!-- Pas de campus -->
      <div
        v-if="!hasCampus"
        class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700"
      >
        Sélectionnez un campus pour afficher les indisponibilités.
      </div>

      <!-- Loading -->
      <div v-else-if="store.loading" class="space-y-2">
        <div v-for="n in 4" :key="n" class="h-14 animate-pulse rounded-xl bg-slate-100" />
      </div>

      <!-- Vide -->
      <div
        v-else-if="store.adminIndisponibilites.length === 0"
        class="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-200 py-12 text-slate-400"
      >
        <Users class="size-10 opacity-40" />
        <p class="text-sm">Aucune indisponibilité pour cette sélection</p>
      </div>

      <!-- Tableau desktop / cartes mobile -->
      <div v-else>
        <div
          class="hidden overflow-hidden rounded-xl border border-slate-100 bg-white shadow-sm sm:block"
        >
          <table class="w-full text-sm">
            <thead
              class="border-b border-slate-100 bg-slate-50 text-xs font-semibold tracking-wide text-slate-500 uppercase"
            >
              <tr>
                <th class="px-4 py-3 text-left">Membre</th>
                <th class="px-4 py-3 text-left">Ministère</th>
                <th class="px-4 py-3 text-left">Du</th>
                <th class="px-4 py-3 text-left">Au</th>
                <th class="px-4 py-3 text-left">Motif</th>
                <th class="px-4 py-3 text-left">Statut</th>
                <th class="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
              <tr
                v-for="item in store.adminIndisponibilites"
                :key="item.id"
                class="transition-colors hover:bg-slate-50/60"
              >
                <td class="px-4 py-3 font-medium text-slate-800">
                  {{ item.membre_prenom }} {{ item.membre_nom }}
                </td>
                <td class="px-4 py-3 text-slate-600">{{ item.ministere_libelle ?? 'Global' }}</td>
                <td class="px-4 py-3 text-slate-600">{{ formatDate(item.date_debut) }}</td>
                <td class="px-4 py-3 text-slate-600">{{ formatDate(item.date_fin) }}</td>
                <td class="max-w-48 px-4 py-3 text-slate-500">
                  <span class="line-clamp-1">{{ item.motif ?? '—' }}</span>
                </td>
                <td class="px-4 py-3">
                  <span :class="['badge', item.validee ? 'badge-green' : 'badge-amber']">
                    <component :is="item.validee ? CheckCircle2 : AlertCircle" class="size-3" />
                    {{ item.validee ? 'Validée' : 'En attente' }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-1">
                    <button
                      v-if="!item.validee"
                      class="action-btn text-emerald-600 hover:bg-emerald-50"
                      title="Valider"
                      @click="handleValider(item.id)"
                    >
                      <CheckCheck class="size-4" />
                    </button>
                    <button
                      class="action-btn text-red-500 hover:bg-red-50"
                      title="Supprimer"
                      @click="handleDelete(item.id)"
                    >
                      <Trash2 class="size-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Cartes mobile -->
        <div class="space-y-3 sm:hidden">
          <div
            v-for="item in store.adminIndisponibilites"
            :key="item.id"
            class="rounded-xl border border-slate-100 bg-white p-4 shadow-sm"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 space-y-1">
                <p class="font-medium text-slate-800">
                  {{ item.membre_prenom }} {{ item.membre_nom }}
                </p>
                <p class="text-xs text-slate-500">{{ item.ministere_libelle ?? 'Global' }}</p>
                <p class="text-sm text-slate-700">
                  {{ formatDate(item.date_debut) }} → {{ formatDate(item.date_fin) }}
                </p>
                <p v-if="item.motif" class="line-clamp-2 text-xs text-slate-500">
                  {{ item.motif }}
                </p>
                <span :class="['badge', item.validee ? 'badge-green' : 'badge-amber']">
                  <component :is="item.validee ? CheckCircle2 : AlertCircle" class="size-3" />
                  {{ item.validee ? 'Validée' : 'En attente' }}
                </span>
              </div>
              <div class="flex flex-col gap-1">
                <button
                  v-if="!item.validee"
                  class="action-btn text-emerald-600 hover:bg-emerald-50"
                  @click="handleValider(item.id)"
                >
                  <CheckCheck class="size-4" />
                </button>
                <button
                  class="action-btn text-red-500 hover:bg-red-50"
                  @click="handleDelete(item.id)"
                >
                  <Trash2 class="size-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Section membre : mes indisponibilités -->
    <template v-else>
      <div v-if="store.loading" class="space-y-2">
        <div v-for="n in 3" :key="n" class="h-14 animate-pulse rounded-xl bg-slate-100" />
      </div>

      <div
        v-else-if="store.myIndisponibilites.length === 0"
        class="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-200 py-12 text-slate-400"
      >
        <CalendarOff class="size-10 opacity-40" />
        <p class="text-sm">Aucune indisponibilité déclarée</p>
        <button
          class="mt-1 rounded-lg px-4 py-2 text-sm font-medium text-white"
          style="background-color: var(--color-primary-600)"
          @click="drawerOpen = true"
        >
          Déclarer une indisponibilité
        </button>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="item in store.myIndisponibilites"
          :key="item.id"
          class="flex items-center gap-4 rounded-xl border border-slate-100 bg-white p-4 shadow-sm"
        >
          <div class="flex size-10 shrink-0 items-center justify-center rounded-xl bg-amber-50">
            <CalendarOff class="size-5 text-amber-500" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="font-semibold text-slate-800">
              {{ formatDate(item.date_debut) }} → {{ formatDate(item.date_fin) }}
            </p>
            <p v-if="item.motif" class="mt-0.5 text-xs text-slate-500">{{ item.motif }}</p>
            <p v-if="item.ministere_libelle" class="mt-0.5 text-xs text-slate-400">
              {{ item.ministere_libelle }}
            </p>
          </div>
          <span :class="['badge', item.validee ? 'badge-green' : 'badge-amber']">
            <component :is="item.validee ? CheckCircle2 : AlertCircle" class="size-3" />
            {{ item.validee ? 'Validée' : 'En attente' }}
          </span>
          <button
            v-if="!item.validee"
            class="action-btn text-red-400 hover:bg-red-50"
            title="Supprimer"
            @click="handleDeleteMine(item.id)"
          >
            <Trash2 class="size-4" />
          </button>
        </div>
      </div>
    </template>

    <!-- ── Drawer de création ── -->
    <AppDrawer
      :isOpen="drawerOpen"
      title="Déclarer une indisponibilité"
      initialSize="standard"
      @close="drawerOpen = false"
    >
      <div class="flex flex-col gap-5">
        <p class="text-sm text-slate-500">
          Indiquez la période durant laquelle vous ne serez pas disponible. Les responsables seront
          notifiés.
        </p>

        <!-- Période -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
              >Du *</label
            >
            <input
              v-model="newForm.date_debut"
              type="date"
              :min="todayDate"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase"
              >Au *</label
            >
            <input
              v-model="newForm.date_fin"
              type="date"
              :min="newForm.date_debut || todayDate"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
            />
          </div>
        </div>

        <!-- Ministère (optionnel) -->
        <div v-if="campusMinisteres.length > 0">
          <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Ministère <span class="font-normal text-slate-400 normal-case">(optionnel)</span>
          </label>
          <select
            v-model="newForm.ministere_id"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-blue-400 focus:outline-none"
          >
            <option value="">Tous mes ministères</option>
            <option v-for="m in campusMinisteres" :key="m.id" :value="m.id">{{ m.nom }}</option>
          </select>
        </div>

        <!-- Motif -->
        <div>
          <label class="mb-1.5 block text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Motif <span class="font-normal text-slate-400 normal-case">(optionnel)</span>
          </label>
          <textarea
            v-model="newForm.motif"
            rows="3"
            placeholder="Vacances, maladie, déplacement..."
            class="w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-300 focus:border-blue-400 focus:outline-none"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex gap-3">
          <button
            class="flex-1 rounded-lg border border-slate-200 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50"
            @click="drawerOpen = false"
          >
            Annuler
          </button>
          <button
            :disabled="!isFormValid || store.loading"
            class="flex-1 rounded-lg py-2 text-sm font-semibold text-white transition-all active:scale-95 disabled:opacity-40"
            style="background-color: var(--color-primary-600)"
            @click="handleSubmit"
          >
            {{ store.loading ? 'Enregistrement…' : 'Déclarer' }}
          </button>
        </div>
      </template>
    </AppDrawer>
  </div>
</template>

<style scoped>
@reference "~~/layers/base/app/assets/css/main.css";

.badge {
  @apply inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold;
}

.badge-green {
  @apply bg-emerald-50 text-emerald-700;
}

.badge-amber {
  @apply bg-amber-50 text-amber-700;
}

.action-btn {
  @apply rounded-lg p-1.5 transition-colors;
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
</style>
