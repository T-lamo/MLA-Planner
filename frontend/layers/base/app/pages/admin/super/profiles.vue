<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChevronDown, Users } from 'lucide-vue-next'
import ProfileCard from '../../../components/profile/ProfileCard.vue'
import ProfileFormDrawer from '../../../components/profile/ProfileFormDrawer.vue'

import type {
  ProfilReadFull,
  ProfilCreateFull,
  ProfilUpdateFull,
} from '~~/layers/base/types/profiles'
import type { CampusRead } from '~~/layers/base/types/campus'
import type { MinistereReadWithRelations } from '~~/layers/base/types/ministere'
import { ProfileRepository } from '~~/layers/base/app/repositories/ProfileRepository'

definePageMeta({ layout: 'default' })

const repo = new ProfileRepository()
const { fetchDetailedMinisteres } = useCampuses()

// --- STATE ---
const allCampuses = ref<CampusRead[]>([])
const selectedCampusId = ref<string | null>(null)
const profiles = ref<ProfilReadFull[]>([])
const isFetching = ref(false)
const searchQuery = ref('')
const isDrawerOpen = ref(false)
const isSubmitting = ref(false)
const editingProfile = ref<ProfilReadFull | null>(null)
const formMinisteres = ref<MinistereReadWithRelations[]>([])
const isCampusDropdownOpen = ref(false)

// --- COMPUTED ---
const selectedCampus = computed(
  () => allCampuses.value.find((c) => c.id === selectedCampusId.value) ?? null,
)

const filteredProfiles = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return profiles.value
  return profiles.value.filter(
    (p) =>
      p.nom.toLowerCase().includes(q) ||
      p.prenom.toLowerCase().includes(q) ||
      p.email.toLowerCase().includes(q),
  )
})

// --- CHARGEMENT ---
const loadProfiles = async (campusId: string) => {
  isFetching.value = true
  try {
    profiles.value = await repo.getAllByCampusFull(campusId)
  } finally {
    isFetching.value = false
  }
}

const selectCampus = async (campusId: string) => {
  selectedCampusId.value = campusId
  isCampusDropdownOpen.value = false
  await loadProfiles(campusId)
  formMinisteres.value = await fetchDetailedMinisteres(campusId)
}

onMounted(async () => {
  allCampuses.value = await repo.getAllCampuses()
  const first = allCampuses.value[0]
  if (first) {
    await selectCampus(first.id)
  }
})

// --- DRAWER ---
const handleOpenCreate = () => {
  editingProfile.value = null
  isDrawerOpen.value = true
}

const handleOpenEdit = (profile: ProfilReadFull) => {
  editingProfile.value = profile
  isDrawerOpen.value = true
}

const handleCampusChangedInForm = async (campusId: string) => {
  formMinisteres.value = await fetchDetailedMinisteres(campusId)
}

const handleFormSubmit = async (formData: ProfilCreateFull) => {
  isSubmitting.value = true
  try {
    if (editingProfile.value) {
      const updatePayload: ProfilUpdateFull = {
        nom: formData.nom,
        prenom: formData.prenom,
        email: formData.email,
        telephone: formData.telephone,
        actif: formData.actif,
        campus_ids: formData.campus_ids,
        campus_principal_id: formData.campus_principal_id ?? null,
        ministere_ids: formData.ministere_ids,
        pole_ids: formData.pole_ids,
        role_codes: formData.role_codes,
      }
      if (formData.utilisateur) {
        updatePayload.utilisateur = {
          username: formData.utilisateur.username,
          actif: formData.utilisateur.actif,
        }
        if (formData.utilisateur.password) {
          updatePayload.utilisateur.password = formData.utilisateur.password
        }
        if (formData.utilisateur.roles_ids?.length) {
          updatePayload.utilisateur.roles_ids = formData.utilisateur.roles_ids
        }
      }
      await repo.update(editingProfile.value.id, updatePayload)
    } else {
      const createPayload: ProfilCreateFull = {
        ...formData,
        utilisateur: formData.utilisateur
          ? { ...formData.utilisateur, password: formData.utilisateur.password || undefined }
          : formData.utilisateur,
      }
      await repo.create(createPayload)
    }
    isDrawerOpen.value = false
    if (selectedCampusId.value) await loadProfiles(selectedCampusId.value)
  } catch {
    // errors handled by global fetch interceptor
  } finally {
    isSubmitting.value = false
  }
}

const handleDelete = async (id: string) => {
  if (confirm('Êtes-vous sûr de vouloir supprimer ce profil ?')) {
    await repo.delete(id)
    if (selectedCampusId.value) await loadProfiles(selectedCampusId.value)
  }
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 md:p-8">
    <!-- En-tête -->
    <div class="flex flex-col gap-1">
      <div class="flex items-center gap-2">
        <Users class="size-5 text-(--color-primary-600)" />
        <h1 class="text-xl font-bold text-slate-800">Tous les profils</h1>
      </div>
      <p class="text-sm text-slate-500">Vue SuperAdmin — accès à tous les campus</p>
    </div>

    <!-- Sélecteur de campus -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="relative">
        <button
          class="flex min-w-48 items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50"
          @click="isCampusDropdownOpen = !isCampusDropdownOpen"
        >
          <span>{{ selectedCampus?.nom ?? 'Choisir un campus' }}</span>
          <ChevronDown
            :class="[
              'size-4 text-slate-400 transition-transform',
              isCampusDropdownOpen ? 'rotate-180' : '',
            ]"
          />
        </button>

        <div
          v-if="isCampusDropdownOpen"
          class="absolute top-full left-0 z-10 mt-1 w-full min-w-56 rounded-xl border border-slate-200 bg-white py-1"
          style="box-shadow: 0 4px 16px rgb(0 0 0 / 0.08)"
        >
          <button
            v-for="campus in allCampuses"
            :key="campus.id"
            class="flex w-full items-center px-4 py-2 text-left text-sm transition-colors hover:bg-slate-50"
            :class="[
              campus.id === selectedCampusId
                ? 'font-semibold text-(--color-primary-700)'
                : 'text-slate-700',
            ]"
            @click="selectCampus(campus.id)"
          >
            {{ campus.nom }}
          </button>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <!-- Barre de recherche -->
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher un membre..."
          class="form-input w-full sm:w-64"
        />

        <button class="btn btn-primary shrink-0" @click="handleOpenCreate">+ Nouveau</button>
      </div>
    </div>

    <!-- Compteur -->
    <p class="text-sm text-slate-500">
      {{ filteredProfiles.length }} membre{{ filteredProfiles.length !== 1 ? 's' : '' }}
      <template v-if="selectedCampus"> — {{ selectedCampus.nom }}</template>
    </p>

    <!-- Squelette de chargement -->
    <div v-if="isFetching" class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="n in 6" :key="n" class="h-20 animate-pulse rounded-xl bg-slate-100"></div>
    </div>

    <!-- Message campus non sélectionné -->
    <div
      v-else-if="!selectedCampusId"
      class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700"
    >
      Sélectionnez un campus pour afficher ses membres.
    </div>

    <!-- Liste vide -->
    <div
      v-else-if="filteredProfiles.length === 0"
      class="rounded-xl border border-slate-100 bg-slate-50 p-8 text-center text-sm text-slate-500"
    >
      Aucun profil trouvé pour ce campus.
    </div>

    <!-- Grille des profils -->
    <TransitionGroup
      v-else
      name="profile-list"
      tag="div"
      class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
    >
      <ProfileCard
        v-for="profile in filteredProfiles"
        :key="profile.id"
        :profile="profile"
        @edit="handleOpenEdit"
        @delete="handleDelete"
      />
    </TransitionGroup>

    <!-- Drawer de formulaire -->
    <ProfileFormDrawer
      :isOpen="isDrawerOpen"
      :editingProfile="editingProfile"
      :campuses="allCampuses"
      :prefillCampusId="editingProfile ? undefined : selectedCampusId"
      :ministeresDetailed="formMinisteres"
      :isSubmitting="isSubmitting"
      @close="isDrawerOpen = false"
      @submit="handleFormSubmit"
      @campus-changed="handleCampusChangedInForm"
    />
  </div>
</template>

<style scoped>
@reference "../../../assets/css/main.css";

.profile-list-enter-active,
.profile-list-leave-active {
  transition: all 0.3s ease;
}
.profile-list-enter-from,
.profile-list-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
.profile-list-move {
  transition: transform 0.3s ease;
}
</style>
