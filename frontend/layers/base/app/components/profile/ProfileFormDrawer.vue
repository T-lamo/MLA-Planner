<script setup lang="ts">
import { ref, watch } from 'vue'
import { User, MapPin, Building2, ShieldCheck, Info } from 'lucide-vue-next'
import { useProfileFormLogic } from '../../composables/useProfileFormLogic'
import FormSection from '../FormSection.vue'

// Import des sous-composants atomiques
import ProfileBasicInfo from './ProfileBasicInfo.vue'
import ProfileCampusSelector from './ProfileCampusSelector.vue'
import ProfileMinistereManager from './ProfileMinistereManager.vue'
import ProfileSecurityAccess from './ProfileSecurityAccess.vue'

import type { ProfilCreateFull, ProfilReadFull } from '~~/layers/base/types/profiles'
import type { CampusRead } from '~~/layers/base/types/campus'
import type { MinistereReadWithRelations } from '~~/layers/base/types/ministere'

interface Props {
  isOpen: boolean
  editingProfile: ProfilReadFull | null
  campuses: CampusRead[]
  ministeresDetailed: MinistereReadWithRelations[]
  isSubmitting: boolean
  isLoadingReferences?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'submit'])

const { mapProfileToForm, toggleMinistere, togglePole } = useProfileFormLogic()

// --- ÉTAT DU FORMULAIRE ---
const form = ref<ProfilCreateFull>({
  nom: '',
  prenom: '',
  email: '',
  telephone: '',
  actif: true,
  campus_ids: [],
  ministere_ids: [],
  pole_ids: [],
  utilisateur: undefined,
})

// --- GESTION DES SECTIONS PLIABLES ---
// On utilise un Set pour permettre l'ouverture de plusieurs sections simultanément
const activeSections = ref(new Set(['basic']))

const toggleSection = (id: string) => {
  if (activeSections.value.has(id)) {
    activeSections.value.delete(id)
  } else {
    activeSections.value.add(id)
  }
}

// --- LOGIQUE DE PRÉ-REMPLISSAGE ---
watch(
  () => props.isOpen,
  (open) => {
    if (!open) return
    if (props.editingProfile) {
      form.value = mapProfileToForm(props.editingProfile)
      // En édition, on ouvre souvent les sections avec du contenu
      if (form.value.campus_ids.length > 0) activeSections.value.add('campus')
      if (form.value.ministere_ids.length > 0) activeSections.value.add('ministeres')
    } else {
      resetForm()
    }
  },
  { immediate: true },
)

const resetForm = () => {
  form.value = {
    nom: '',
    prenom: '',
    email: '',
    telephone: '',
    actif: true,
    campus_ids: [],
    ministere_ids: [],
    pole_ids: [],
    utilisateur: undefined,
  }
  activeSections.value = new Set(['basic'])
}

// --- HANDLERS ÉVÉNEMENTS ---
const onToggleMin = (min: MinistereReadWithRelations) => {
  const res = toggleMinistere(min, form.value.ministere_ids, form.value.pole_ids)
  form.value.ministere_ids = res.ministere_ids
  form.value.pole_ids = res.pole_ids
}

const onTogglePole = (mId: string, pId: string) => {
  const res = togglePole(
    mId,
    pId,
    props.ministeresDetailed,
    form.value.ministere_ids,
    form.value.pole_ids,
  )
  form.value.ministere_ids = res.ministere_ids
  form.value.pole_ids = res.pole_ids
}

const handleSubmit = () => {
  const payload = JSON.parse(JSON.stringify(form.value))
  emit('submit', payload)
}
</script>

<template>
  <AppDrawer
    :isOpen="isOpen"
    :title="
      editingProfile
        ? `Édition : ${editingProfile.prenom} ${editingProfile.nom}`
        : 'Nouveau Collaborateur'
    "
    initialSize="half"
    @close="emit('close')"
  >
    <form id="profileForm" class="flex flex-col gap-2 pb-10" @submit.prevent="handleSubmit">
      <FormSection
        title="Informations Personnelles"
        :icon="User"
        :isOpen="activeSections.has('basic')"
        @toggle="toggleSection('basic')"
      >
        <ProfileBasicInfo v-model="form" />
      </FormSection>

      <FormSection
        title="Affectation Campus"
        :icon="MapPin"
        :isOpen="activeSections.has('campus')"
        :badge="form.campus_ids.length > 0 ? form.campus_ids.length : undefined"
        @toggle="toggleSection('campus')"
      >
        <ProfileCampusSelector v-model="form.campus_ids" :campuses="campuses" />
      </FormSection>

      <FormSection
        title="Ministères & Pôles"
        :icon="Building2"
        :isOpen="activeSections.has('ministeres')"
        :badge="form.pole_ids.length > 0 ? form.pole_ids.length : undefined"
        @toggle="toggleSection('ministeres')"
      >
        <ProfileMinistereManager
          :ministeres="ministeresDetailed"
          :ministereIds="form.ministere_ids"
          :poleIds="form.pole_ids"
          @toggle-ministere="onToggleMin"
          @toggle-pole="onTogglePole"
        />
      </FormSection>

      <FormSection
        title="Accès Applicatif"
        :icon="ShieldCheck"
        :isOpen="activeSections.has('security')"
        :badge="form.utilisateur ? 'Actif' : undefined"
        @toggle="toggleSection('security')"
      >
        <ProfileSecurityAccess v-model="form.utilisateur" />
      </FormSection>

      <div class="mt-4 flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50/50 p-4">
        <Info class="mt-0.5 size-4 text-blue-500" />
        <p class="text-[11px] leading-relaxed text-blue-700">
          Les modifications sur les accès applicatifs prendront effet lors de la prochaine
          reconnexion de l'utilisateur.
        </p>
      </div>
    </form>

    <template #footer>
      <div class="flex w-full items-center gap-3">
        <button type="button" class="footer-btn-secondary" @click="emit('close')">Annuler</button>
        <button
          type="submit"
          form="profileForm"
          :disabled="isSubmitting"
          class="footer-btn-primary"
        >
          <span v-if="isSubmitting">Traitement...</span>
          <span v-else>{{
            editingProfile ? 'Enregistrer les modifications' : 'Créer le profil'
          }}</span>
        </button>
      </div>
    </template>
  </AppDrawer>
</template>

<style scoped>
@reference "../../assets/css/main.css";

/* Conteneur principal du formulaire avec padding horizontal */
#profileForm {
  @apply px-2;
}

/* Boutons de Footer */
.footer-btn-primary {
  @apply flex-1 rounded-xl py-3 text-xs font-bold text-white transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50;
  background-color: var(--color-primary-600);
}

.footer-btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-700);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-primary-600) 25%, transparent);
}

.footer-btn-secondary {
  @apply flex-1 rounded-xl border border-slate-200 py-3 text-xs font-bold text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700;
}

/* On garde les utilitaires de scroll au cas où le contenu déborde */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
</style>
