<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Building2, Globe, Plus, Pencil, Trash2, X } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import type { OrganisationRead } from '~~/layers/base/types/organisation'
import type { CampusRead } from '~~/layers/base/types/campus'
import type { PaysRead } from '~~/layers/base/types/pays'

definePageMeta({ layout: 'default' })

const authStore = useAuthStore()

if (!authStore.isSuperAdmin) {
  await navigateTo('/admin/profiles')
}

const {
  organisations,
  isFetching: isFetchingOrgs,
  create: createOrg,
  update: updateOrg,
  remove: removeOrg,
  refresh: refreshOrgs,
} = useOrganisations()
const {
  allPays,
  isFetching: isFetchingPays,
  create: createPays,
  update: updatePays,
  remove: removePays,
  refresh: refreshPays,
} = usePaysAdmin()
const {
  allCampuses,
  isFetching: isFetchingCampuses,
  create: createCampus,
  update: updateCampus,
  remove: removeCampus,
  refresh: refreshCampuses,
} = useCampusAdmin()
const { confirm } = useMLAConfirm()

onMounted(async () => {
  await Promise.all([refreshOrgs(), refreshPays(), refreshCampuses()])
})

const TIMEZONES = [
  'Europe/Paris',
  'Africa/Abidjan',
  'Africa/Dakar',
  'America/New_York',
  'America/Toronto',
  'America/Montreal',
  'Europe/London',
  'Europe/Brussels',
]

// --- Organisation form state ---
const isOrgFormOpen = ref(false)
const editingOrg = ref<OrganisationRead | null>(null)
const isSubmittingOrg = ref(false)
const orgForm = ref({ nom: '', date_creation: '' })

const openOrgCreate = () => {
  editingOrg.value = null
  orgForm.value = { nom: '', date_creation: '' }
  isOrgFormOpen.value = true
}

const openOrgEdit = (org: OrganisationRead) => {
  editingOrg.value = org
  orgForm.value = { nom: org.nom, date_creation: org.date_creation }
  isOrgFormOpen.value = true
}

const cancelOrgForm = () => {
  isOrgFormOpen.value = false
  editingOrg.value = null
}

const handleOrgSubmit = async () => {
  isSubmittingOrg.value = true
  try {
    if (editingOrg.value) {
      await updateOrg(editingOrg.value.id, { nom: orgForm.value.nom })
    } else {
      await createOrg({ nom: orgForm.value.nom, date_creation: orgForm.value.date_creation })
    }
    isOrgFormOpen.value = false
    editingOrg.value = null
  } catch {
    // errors handled by global fetch interceptor
  } finally {
    isSubmittingOrg.value = false
  }
}

const handleOrgDelete = async (org: OrganisationRead) => {
  const confirmed = await confirm(
    'Supprimer cette organisation ?',
    `L'organisation "${org.nom}" sera supprimée définitivement.`,
  )
  if (confirmed) await removeOrg(org.id)
}

// --- Pays form state ---
const isPaysFormOpen = ref(false)
const editingPays = ref<PaysRead | null>(null)
const isSubmittingPays = ref(false)
const paysForm = ref({ nom: '', code: '', organisation_id: '' })

const openPaysCreate = () => {
  editingPays.value = null
  paysForm.value = { nom: '', code: '', organisation_id: '' }
  isPaysFormOpen.value = true
}

const openPaysEdit = (p: PaysRead) => {
  editingPays.value = p
  paysForm.value = { nom: p.nom, code: p.code, organisation_id: p.organisation_id }
  isPaysFormOpen.value = true
}

const cancelPaysForm = () => {
  isPaysFormOpen.value = false
  editingPays.value = null
}

const handlePaysSubmit = async () => {
  isSubmittingPays.value = true
  try {
    if (editingPays.value) {
      await updatePays(editingPays.value.id, {
        nom: paysForm.value.nom,
        code: paysForm.value.code,
        organisation_id: paysForm.value.organisation_id,
      })
    } else {
      await createPays({
        nom: paysForm.value.nom,
        code: paysForm.value.code,
        organisation_id: paysForm.value.organisation_id,
      })
    }
    isPaysFormOpen.value = false
    editingPays.value = null
  } catch {
    // errors handled by global fetch interceptor
  } finally {
    isSubmittingPays.value = false
  }
}

const handlePaysDelete = async (p: PaysRead) => {
  const confirmed = await confirm(
    'Supprimer ce pays ?',
    `Le pays "${p.nom}" sera supprimé définitivement.`,
  )
  if (confirmed) await removePays(p.id)
}

const getOrgNom = (orgId: string): string => {
  return organisations.value.find((o) => o.id === orgId)?.nom ?? orgId
}

// --- Campus drawer state ---
const isCampusDrawerOpen = ref(false)
const editingCampus = ref<CampusRead | null>(null)
const isSubmittingCampus = ref(false)
const campusForm = ref({ nom: '', ville: '', timezone: 'Europe/Paris', pays_id: '' })

const openCampusCreate = () => {
  editingCampus.value = null
  campusForm.value = { nom: '', ville: '', timezone: 'Europe/Paris', pays_id: '' }
  isCampusDrawerOpen.value = true
}

const openCampusEdit = (campus: CampusRead) => {
  editingCampus.value = campus
  campusForm.value = {
    nom: campus.nom,
    ville: campus.ville,
    timezone: campus.timezone,
    pays_id: campus.pays_id,
  }
  isCampusDrawerOpen.value = true
}

const closeCampusDrawer = () => {
  isCampusDrawerOpen.value = false
  editingCampus.value = null
}

const handleCampusSubmit = async () => {
  isSubmittingCampus.value = true
  try {
    if (editingCampus.value) {
      await updateCampus(editingCampus.value.id, {
        nom: campusForm.value.nom,
        ville: campusForm.value.ville,
        timezone: campusForm.value.timezone,
        pays_id: campusForm.value.pays_id,
      })
    } else {
      await createCampus({
        nom: campusForm.value.nom,
        ville: campusForm.value.ville,
        timezone: campusForm.value.timezone,
        pays_id: campusForm.value.pays_id,
      })
    }
    isCampusDrawerOpen.value = false
    editingCampus.value = null
  } catch {
    // errors handled by global fetch interceptor
  } finally {
    isSubmittingCampus.value = false
  }
}

const handleCampusDelete = async (campus: CampusRead) => {
  const confirmed = await confirm(
    'Supprimer ce campus ?',
    `Le campus "${campus.nom}" sera supprimé définitivement.`,
  )
  if (confirmed) await removeCampus(campus.id)
}

const getPaysNom = (paysId: string): string => {
  return allPays.value.find((p) => p.id === paysId)?.nom ?? paysId
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 md:p-8">
    <!-- En-tête -->
    <div class="flex items-center gap-3">
      <div class="flex size-10 items-center justify-center rounded-xl bg-(--color-primary-50)">
        <Building2 class="size-5 text-(--color-primary-700)" />
      </div>
      <div>
        <h1 class="text-xl font-bold text-slate-900">Campuses & Organisations</h1>
        <p class="mt-0.5 text-sm text-slate-500">Gérez les organisations, pays et campus.</p>
      </div>
    </div>

    <!-- Section Organisations -->
    <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <h2 class="text-base font-semibold text-slate-800">Organisations</h2>
        <button
          v-if="!isOrgFormOpen"
          class="btn btn-primary btn-sm"
          :disabled="isFetchingOrgs"
          @click="openOrgCreate"
        >
          <Plus class="size-4" />
          Nouvelle organisation
        </button>
      </div>

      <div class="px-6 py-4">
        <!-- Formulaire inline -->
        <div
          v-if="isOrgFormOpen"
          class="mb-4 rounded-xl border border-(--color-primary-100) bg-(--color-primary-50) p-4"
        >
          <p class="mb-3 text-sm font-medium text-(--color-primary-700)">
            {{ editingOrg ? "Modifier l'organisation" : 'Nouvelle organisation' }}
          </p>
          <div class="flex flex-col gap-3 sm:flex-row">
            <input
              v-model="orgForm.nom"
              type="text"
              placeholder="Nom (ex: Nouvelle organisation)"
              class="form-input flex-1"
            />
            <input
              v-if="!editingOrg"
              v-model="orgForm.date_creation"
              type="date"
              class="form-input w-44"
            />
            <div class="flex gap-2">
              <button
                class="btn btn-primary"
                :disabled="isSubmittingOrg || !orgForm.nom.trim()"
                @click="handleOrgSubmit"
              >
                Enregistrer
              </button>
              <button class="btn btn-secondary" @click="cancelOrgForm">Annuler</button>
            </div>
          </div>
        </div>

        <!-- Liste des organisations -->
        <div v-if="isFetchingOrgs && organisations.length === 0" class="space-y-2">
          <div v-for="n in 2" :key="n" class="h-12 animate-pulse rounded-lg bg-slate-100" />
        </div>

        <div v-else-if="organisations.length === 0 && !isOrgFormOpen">
          <p class="text-sm text-slate-400 italic">
            Aucune organisation. Créez la première organisation.
          </p>
        </div>

        <ul v-else class="divide-y divide-slate-100">
          <li
            v-for="org in organisations"
            :key="org.id"
            class="flex items-center justify-between py-3"
          >
            <div class="flex items-center gap-3">
              <span
                class="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-xs font-medium text-slate-600"
              >
                {{ org.pays.length }} pays
              </span>
              <span class="text-sm font-medium text-slate-800">{{ org.nom }}</span>
              <span class="text-xs text-slate-400">{{ org.date_creation }}</span>
            </div>
            <div class="flex items-center gap-1">
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                title="Modifier"
                @click="openOrgEdit(org)"
              >
                <Pencil class="size-4" />
              </button>
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                title="Supprimer"
                @click="handleOrgDelete(org)"
              >
                <Trash2 class="size-4" />
              </button>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <!-- Section Pays -->
    <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div class="flex items-center gap-2">
          <Globe class="size-4 text-slate-500" />
          <h2 class="text-base font-semibold text-slate-800">Pays</h2>
        </div>
        <button
          v-if="!isPaysFormOpen"
          class="btn btn-primary btn-sm"
          :disabled="isFetchingPays || organisations.length === 0"
          @click="openPaysCreate"
        >
          <Plus class="size-4" />
          Nouveau pays
        </button>
      </div>

      <div class="px-6 py-4">
        <!-- Formulaire inline -->
        <div
          v-if="isPaysFormOpen"
          class="mb-4 rounded-xl border border-(--color-primary-100) bg-(--color-primary-50) p-4"
        >
          <p class="mb-3 text-sm font-medium text-(--color-primary-700)">
            {{ editingPays ? 'Modifier le pays' : 'Nouveau pays' }}
          </p>
          <div class="flex flex-col gap-3">
            <div class="flex flex-col gap-3 sm:flex-row">
              <input
                v-model="paysForm.nom"
                type="text"
                placeholder="Nom (ex: France)"
                class="form-input flex-1"
              />
              <input
                v-model="paysForm.code"
                type="text"
                placeholder="Code ISO (ex: FR)"
                class="form-input w-28 uppercase"
              />
            </div>
            <div class="flex flex-col gap-3 sm:flex-row">
              <div class="form-select-wrapper flex-1">
                <select v-model="paysForm.organisation_id" class="form-input form-select">
                  <option value="" disabled>Sélectionner une organisation</option>
                  <option v-for="org in organisations" :key="org.id" :value="org.id">
                    {{ org.nom }}
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
              <div class="flex gap-2">
                <button
                  class="btn btn-primary"
                  :disabled="
                    isSubmittingPays ||
                    !paysForm.nom.trim() ||
                    !paysForm.code.trim() ||
                    !paysForm.organisation_id
                  "
                  @click="handlePaysSubmit"
                >
                  Enregistrer
                </button>
                <button class="btn btn-secondary" @click="cancelPaysForm">Annuler</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Liste des pays -->
        <div v-if="isFetchingPays && allPays.length === 0" class="space-y-2">
          <div v-for="n in 2" :key="n" class="h-12 animate-pulse rounded-lg bg-slate-100" />
        </div>

        <div v-else-if="allPays.length === 0 && !isPaysFormOpen">
          <p class="text-sm text-slate-400 italic">
            Aucun pays. Créez d'abord une organisation, puis ajoutez un pays.
          </p>
        </div>

        <ul v-else class="divide-y divide-slate-100">
          <li v-for="p in allPays" :key="p.id" class="flex items-center justify-between py-3">
            <div class="flex items-center gap-3">
              <span
                class="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-xs font-semibold text-slate-600"
              >
                {{ p.code }}
              </span>
              <span class="text-sm font-medium text-slate-800">{{ p.nom }}</span>
              <span
                class="rounded-full bg-(--color-primary-50) px-2 py-0.5 text-xs text-(--color-primary-700)"
              >
                {{ getOrgNom(p.organisation_id) }}
              </span>
            </div>
            <div class="flex items-center gap-1">
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                title="Modifier"
                @click="openPaysEdit(p)"
              >
                <Pencil class="size-4" />
              </button>
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                title="Supprimer"
                @click="handlePaysDelete(p)"
              >
                <Trash2 class="size-4" />
              </button>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <!-- Section Campuses -->
    <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <h2 class="text-base font-semibold text-slate-800">Campuses</h2>
        <button
          class="btn btn-primary btn-sm"
          :disabled="isFetchingCampuses"
          @click="openCampusCreate"
        >
          <Plus class="size-4" />
          Nouveau campus
        </button>
      </div>

      <div class="px-6 py-4">
        <!-- État chargement -->
        <div v-if="isFetchingCampuses && allCampuses.length === 0" class="space-y-2">
          <div v-for="n in 3" :key="n" class="h-16 animate-pulse rounded-xl bg-slate-100" />
        </div>

        <!-- État vide -->
        <div
          v-else-if="allCampuses.length === 0"
          class="flex flex-col items-center gap-3 py-10 text-center"
        >
          <div class="flex size-14 items-center justify-center rounded-2xl bg-slate-100">
            <Building2 class="size-7 text-slate-400" />
          </div>
          <div>
            <p class="text-sm font-medium text-slate-700">Aucun campus pour l'instant</p>
            <p class="mt-0.5 text-xs text-slate-400">
              Créez le premier campus pour démarrer la configuration.
            </p>
          </div>
          <button class="btn btn-primary mt-1" @click="openCampusCreate">
            <Plus class="size-4" />
            Créer un campus
          </button>
        </div>

        <!-- Liste campuses -->
        <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div
            v-for="campus in allCampuses"
            :key="campus.id"
            class="flex items-start justify-between rounded-xl border border-slate-100 bg-slate-50 p-4"
          >
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold text-slate-800">{{ campus.nom }}</p>
              <p class="mt-0.5 text-xs text-slate-500">{{ campus.ville }}</p>
              <div class="mt-2 flex flex-wrap gap-1.5">
                <span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600">
                  {{ campus.timezone }}
                </span>
                <span
                  class="rounded-full bg-(--color-primary-50) px-2 py-0.5 text-xs text-(--color-primary-700)"
                >
                  {{ getPaysNom(campus.pays_id) }}
                </span>
              </div>
            </div>
            <div class="ml-2 flex shrink-0 items-center gap-1">
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-white hover:text-slate-700"
                title="Modifier"
                @click="openCampusEdit(campus)"
              >
                <Pencil class="size-4" />
              </button>
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                title="Supprimer"
                @click="handleCampusDelete(campus)"
              >
                <Trash2 class="size-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Drawer Campus -->
    <Teleport to="body">
      <Transition name="drawer-fade">
        <div v-if="isCampusDrawerOpen" class="fixed inset-0 z-50 flex justify-end">
          <!-- Overlay -->
          <div
            class="absolute inset-0 bg-slate-900/30 backdrop-blur-sm"
            @click="closeCampusDrawer"
          />

          <!-- Panel -->
          <div class="relative z-10 flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
            <!-- Drawer header -->
            <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
              <h2 class="text-base font-semibold text-slate-900">
                {{ editingCampus ? 'Modifier le campus' : 'Nouveau campus' }}
              </h2>
              <button
                class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                @click="closeCampusDrawer"
              >
                <X class="size-5" />
              </button>
            </div>

            <!-- Drawer body -->
            <div class="flex-1 overflow-y-auto px-6 py-6">
              <div class="space-y-4">
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Nom du campus <span class="text-red-500">*</span>
                  </label>
                  <input
                    v-model="campusForm.nom"
                    type="text"
                    placeholder="Ex: Campus Paris"
                    class="form-input"
                  />
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Ville <span class="text-red-500">*</span>
                  </label>
                  <input
                    v-model="campusForm.ville"
                    type="text"
                    placeholder="Ex: Paris"
                    class="form-input"
                  />
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Fuseau horaire
                  </label>
                  <div class="form-select-wrapper">
                    <select v-model="campusForm.timezone" class="form-input form-select">
                      <option v-for="tz in TIMEZONES" :key="tz" :value="tz">{{ tz }}</option>
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
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">
                    Pays <span class="text-red-500">*</span>
                  </label>
                  <div class="form-select-wrapper">
                    <select v-model="campusForm.pays_id" class="form-input form-select">
                      <option value="" disabled>Sélectionner un pays</option>
                      <option v-for="p in allPays" :key="p.id" :value="p.id">
                        {{ p.nom }} ({{ p.code }})
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
                </div>
              </div>
            </div>

            <!-- Drawer footer -->
            <div class="border-t border-slate-100 px-6 py-4">
              <div class="flex justify-end gap-3">
                <button class="btn btn-secondary" @click="closeCampusDrawer">Annuler</button>
                <button
                  class="btn btn-primary"
                  :disabled="isSubmittingCampus || !campusForm.nom.trim() || !campusForm.pays_id"
                  @click="handleCampusSubmit"
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
@reference "../../assets/css/main.css";

.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 0.25s ease;
}
.drawer-fade-enter-active .relative,
.drawer-fade-leave-active .relative {
  transition: transform 0.25s ease;
}
.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}
</style>
