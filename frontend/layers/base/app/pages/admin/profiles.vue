<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ProfileHeader from '../../components/profile/ProfileHeader.vue'
import ProfileFilters from '../../components/profile/ProfileFilters.vue'
import ProfileCard from '../../components/profile/ProfileCard.vue'
import ProfileFormDrawer from '../../components/profile/ProfileFormDrawer.vue'

// Import des types nécessaires
import type {
  ProfilReadFull,
  ProfilCreateFull,
  ProfilUpdateFull,
} from '~~/layers/base/types/profiles'
import type { CampusRead } from '~~/layers/base/types/campus'
import { ProfileRepository } from '~~/layers/base/app/repositories/ProfileRepository'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'

const authStore = useAuthStore()

const { profiles, isFetching, totalProfiles, activeCampusId, campuses, create, update, remove } =
  useProfiles()

// All campuses for the form selector (admins can assign any campus to a member)
const allCampuses = ref<CampusRead[]>([])
onMounted(async () => {
  try {
    allCampuses.value = await new ProfileRepository().getAllCampuses()
  } catch {
    // Fallback to user's campuses if endpoint unreachable
    allCampuses.value = campuses.value
  }
})

const { ministeresByCampus, fetchDetailedMinisteres } = useCampuses()

// State
const searchQuery = ref('')
const isDrawerOpen = ref(false)
const isSubmitting = ref(false)
const editingProfile = ref<ProfilReadFull | null>(null)

// Watcher intelligent pour charger les données du campus
watch(
  activeCampusId,
  (newId) => {
    if (newId) fetchDetailedMinisteres(newId)
  },
  { immediate: true },
)
// Computed : Filtrage de la liste
const filteredProfiles = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return profiles.value
  return profiles.value.filter(
    (p) =>
      p.nom.toLowerCase().includes(query) ||
      p.prenom.toLowerCase().includes(query) ||
      p.email.toLowerCase().includes(query),
  )
})

// Actions
const handleOpenCreate = () => {
  editingProfile.value = null
  isDrawerOpen.value = true
}

const handleOpenEdit = (profile: ProfilReadFull) => {
  editingProfile.value = profile
  isDrawerOpen.value = true
}

const handleFormSubmit = async (formData: ProfilCreateFull) => {
  isSubmitting.value = true
  try {
    if (editingProfile.value) {
      // Build an explicit ProfilUpdateFull — never send roles_ids in utilisateur:
      // UtilisateurUpdate validator rejects an empty roles_ids array with 422.
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
      await update(editingProfile.value.id, updatePayload)
    } else {
      // Normalize empty password to undefined — backend min_length=6 rejects "".
      const createPayload: ProfilCreateFull = {
        ...formData,
        utilisateur: formData.utilisateur
          ? { ...formData.utilisateur, password: formData.utilisateur.password || undefined }
          : formData.utilisateur,
      }
      await create(createPayload)
    }
    isDrawerOpen.value = false
  } catch {
    // errors are handled by the global fetch interceptor
  } finally {
    isSubmitting.value = false
  }
}

const handleDelete = async (id: string) => {
  if (confirm('Êtes-vous sûr de vouloir supprimer ce profil ?')) {
    await remove(id)
  }
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 md:p-8">
    <ProfileHeader :total="totalProfiles" :isFetching="isFetching" @add="handleOpenCreate" />

    <ProfileFilters
      v-model:searchQuery="searchQuery"
      v-model:activeCampusId="activeCampusId"
      :campuses="campuses"
    />

    <div
      v-if="campuses.length === 0 && !isFetching"
      class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700"
    >
      Aucun campus disponible.
      <template v-if="authStore.isSuperAdmin">
        <RouterLink to="/admin/campuses" class="font-medium underline">
          Créer le premier campus
        </RouterLink>
      </template>
      <template v-else> Contactez un Super Admin pour créer un campus. </template>
    </div>

    <div v-if="isFetching" class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="n in 6" :key="n" class="h-20 animate-pulse rounded-xl bg-slate-100"></div>
    </div>

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
    <ProfileFormDrawer
      :isOpen="isDrawerOpen"
      :editingProfile="editingProfile"
      :campuses="allCampuses"
      :prefillCampusId="editingProfile ? undefined : activeCampusId"
      :ministeresDetailed="ministeresByCampus"
      :isSubmitting="isSubmitting"
      @close="isDrawerOpen = false"
      @submit="handleFormSubmit"
    />
  </div>
</template>

<style scoped>
@reference "../../assets/css/main.css";

/* Animations de liste */
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
