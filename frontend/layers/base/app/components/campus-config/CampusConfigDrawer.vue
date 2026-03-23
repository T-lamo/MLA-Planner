<template>
  <AppDrawer :isOpen="drawerContext.mode !== null" initialSize="standard" @close="closeDrawer">
    <template #header>
      <h3 class="truncate font-bold text-slate-800">{{ drawerTitle }}</h3>
    </template>

    <!-- Formulaire Ministère -->
    <form
      v-if="drawerContext.mode === 'add-ministere' || drawerContext.mode === 'edit-ministere'"
      id="cc-ministere-form"
      class="space-y-4"
      @submit.prevent="handleSubmit"
    >
      <div>
        <label class="mb-1.5 block text-sm font-medium text-slate-700" for="cc-min-nom">
          Nom du ministère <span class="text-red-500">*</span>
        </label>
        <input
          id="cc-min-nom"
          v-model="ministereForm.nom"
          class="cc-input"
          type="text"
          placeholder="Ex : Louange, Accueil…"
          required
          autofocus
        />
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-slate-700" for="cc-min-desc">
          Description
        </label>
        <textarea
          id="cc-min-desc"
          v-model="ministereForm.description"
          class="cc-input resize-none"
          rows="3"
          placeholder="Description optionnelle"
        />
      </div>

      <div v-if="conflictingMinistere" class="rounded-lg border border-amber-200 bg-amber-50 p-3">
        <p class="text-sm font-medium text-amber-800">
          Ce ministère existe déjà — {{ conflictingMinistere.nom }}
        </p>
        <button
          type="button"
          class="mt-2 text-xs font-semibold text-amber-800 underline underline-offset-2 hover:text-amber-900"
          :disabled="isLinkingMinistere"
          @click="handleLinkMinistere"
        >
          {{ isLinkingMinistere ? 'Rattachement…' : 'Rattacher au campus' }}
        </button>
      </div>
    </form>

    <!-- Formulaire Catégorie -->
    <form
      v-else-if="drawerContext.mode === 'add-categorie' || drawerContext.mode === 'edit-categorie'"
      id="cc-categorie-form"
      class="space-y-4"
      @submit.prevent="handleSubmit"
    >
      <div>
        <label class="mb-1.5 block text-sm font-medium text-slate-700" for="cc-cat-nom">
          Libellé de la catégorie <span class="text-red-500">*</span>
        </label>
        <input
          id="cc-cat-nom"
          v-model="categorieForm.nom"
          class="cc-input"
          type="text"
          placeholder="Ex : Chant, Musiciens…"
          required
          autofocus
        />
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-slate-700" for="cc-cat-desc">
          Description
        </label>
        <textarea
          id="cc-cat-desc"
          v-model="categorieForm.description"
          class="cc-input resize-none"
          rows="3"
          placeholder="Description optionnelle"
        />
      </div>
    </form>

    <!-- Formulaire Rôle Compétence -->
    <form
      v-else-if="drawerContext.mode === 'add-role' || drawerContext.mode === 'edit-role'"
      id="cc-role-form"
      class="space-y-4"
      @submit.prevent="handleSubmit"
    >
      <div>
        <label class="mb-1.5 block text-sm font-medium text-slate-700" for="cc-role-code">
          Code <span class="text-red-500">*</span>
        </label>
        <!-- En mode édition : code en lecture seule -->
        <div v-if="isEditMode" class="rounded-md border border-slate-100 bg-slate-50 px-3 py-2">
          <span class="font-mono text-sm font-bold text-slate-700 uppercase">{{
            roleForm.code
          }}</span>
          <span class="ml-2 text-xs text-slate-400">code immuable</span>
        </div>
        <!-- En mode création : champ code éditable -->
        <input
          v-else
          id="cc-role-code"
          v-model="roleForm.code"
          class="cc-input font-mono uppercase"
          type="text"
          placeholder="Ex : SOPRANO, PIANISTE"
          required
          autofocus
          maxlength="20"
        />
        <p v-if="!isEditMode && !conflictingRole" class="mt-1 text-xs text-slate-400">
          Majuscules et underscores uniquement (max 20 caractères)
        </p>

        <!-- Conflit détecté -->
        <div v-if="conflictingRole" class="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
          <p class="text-sm font-medium text-amber-800">
            Ce code existe déjà — {{ conflictingRole.libelle }}
          </p>
          <p class="mt-0.5 text-xs text-amber-700">
            Actuellement dans la catégorie
            <span class="font-mono font-semibold">{{ conflictingRole.categorie_code }}</span>
          </p>
          <button
            type="button"
            class="mt-2 text-xs font-semibold text-amber-800 underline underline-offset-2 hover:text-amber-900"
            :disabled="isLinking"
            @click="handleLinkExisting"
          >
            {{ isLinking ? 'Rattachement…' : 'Rattacher à cette catégorie' }}
          </button>
        </div>
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-slate-700" for="cc-role-libelle">
          Libellé <span class="text-red-500">*</span>
        </label>
        <input
          id="cc-role-libelle"
          v-model="roleForm.libelle"
          class="cc-input"
          type="text"
          placeholder="Ex : Voix Soprano"
          required
        />
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-slate-700" for="cc-role-desc">
          Description
        </label>
        <textarea
          id="cc-role-desc"
          v-model="roleForm.description"
          class="cc-input resize-none"
          rows="2"
          placeholder="Description optionnelle"
        />
      </div>
    </form>

    <template #footer>
      <div class="flex justify-end gap-3">
        <button type="button" class="cc-btn-secondary" @click="closeDrawer">Annuler</button>
        <button
          type="submit"
          :form="activeFormId"
          :disabled="isSubmitting || (!isEditMode && (!!conflictingRole || !!conflictingMinistere))"
          class="cc-btn-primary flex items-center gap-2"
        >
          <Loader2 v-if="isSubmitting" class="size-4 animate-spin" />
          {{ isEditMode ? 'Modifier' : 'Ajouter' }}
        </button>
      </div>
    </template>
  </AppDrawer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import { useCampusConfig } from '../../composables/useCampusConfig'
import { useCampusConfigForm } from '../../composables/useCampusConfigForm'

const campusConfig = useCampusConfig()
const {
  drawerContext,
  isSubmitting,
  ministereForm,
  categorieForm,
  roleForm,
  closeDrawer,
  submitForm,
} = useCampusConfigForm()

const isLinking = ref(false)
const isLinkingMinistere = ref(false)

const conflictingMinistere = computed(() => {
  if (drawerContext.value.mode !== 'add-ministere') return null
  const nom = ministereForm.nom.trim().toLowerCase()
  if (!nom) return null
  const alreadyLinked = campusConfig.ministeres.value.some((m) => m.nom.toLowerCase() === nom)
  if (alreadyLinked) return null
  return campusConfig.allMinisteres.value.find((m) => m.nom.toLowerCase() === nom) ?? null
})

const conflictingRole = computed(() => {
  if (drawerContext.value.mode !== 'add-role') return null
  const code = roleForm.code.trim().toUpperCase()
  if (!code) return null
  return campusConfig.allRoleCompetences.value.find((r) => r.code === code) ?? null
})

const drawerTitle = computed((): string => {
  const mode = drawerContext.value.mode
  if (mode === 'add-ministere') return 'Ajouter un ministère'
  if (mode === 'add-categorie') return 'Ajouter une catégorie'
  if (mode === 'add-role') return 'Ajouter une compétence'
  if (mode === 'edit-ministere') return 'Modifier le ministère'
  if (mode === 'edit-categorie') return 'Modifier la catégorie'
  if (mode === 'edit-role') return 'Modifier la compétence'
  return ''
})

const activeFormId = computed((): string | undefined => {
  const mode = drawerContext.value.mode
  if (mode === 'add-ministere' || mode === 'edit-ministere') return 'cc-ministere-form'
  if (mode === 'add-categorie' || mode === 'edit-categorie') return 'cc-categorie-form'
  if (mode === 'add-role' || mode === 'edit-role') return 'cc-role-form'
  return undefined
})

const isEditMode = computed(() => drawerContext.value.mode?.startsWith('edit-') ?? false)

async function handleSubmit(): Promise<void> {
  await submitForm(campusConfig)
}

async function handleLinkExisting(): Promise<void> {
  const categorieId = drawerContext.value.categorieId
  const role = conflictingRole.value
  if (!role || !categorieId) return
  isLinking.value = true
  try {
    await campusConfig.linkRoleCompetence(categorieId, role.code)
    closeDrawer()
  } catch {
    // Erreur déjà notifiée par l'intercepteur
  } finally {
    isLinking.value = false
  }
}

async function handleLinkMinistere(): Promise<void> {
  const min = conflictingMinistere.value
  if (!min) return
  isLinkingMinistere.value = true
  try {
    await campusConfig.linkMinistere(min.nom)
    closeDrawer()
  } catch {
    // Erreur déjà notifiée par l'intercepteur
  } finally {
    isLinkingMinistere.value = false
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.cc-input {
  @apply w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 transition-colors outline-none focus:border-(--color-primary-400) focus:ring-2 focus:ring-(--color-primary-100);
}

.cc-btn-primary {
  @apply rounded-lg bg-(--color-primary-600) px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:bg-(--color-primary-700) active:scale-95 disabled:cursor-not-allowed disabled:opacity-60;
}

.cc-btn-secondary {
  @apply rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50;
}
</style>
