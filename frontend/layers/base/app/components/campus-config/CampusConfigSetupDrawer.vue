<template>
  <AppDrawer :isOpen="setup.isOpen.value" initialSize="half" @close="setup.close()">
    <template #header>
      <div>
        <h3 class="font-bold text-slate-800">Configuration initiale du campus</h3>
        <p class="mt-0.5 text-xs text-slate-500">
          Définissez la structure complète en une seule opération idempotente
        </p>
      </div>
    </template>

    <form id="campus-setup-form" class="space-y-5" @submit.prevent="handleSubmit">
      <!-- Statuts planning -->
      <label
        class="flex cursor-pointer items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3"
      >
        <input
          v-model="setup.form.value.init_statuts"
          type="checkbox"
          class="mt-0.5 size-4 rounded border-amber-300 accent-(--color-primary-600)"
        />
        <div>
          <p class="text-sm font-semibold text-amber-800">Initialiser les statuts</p>
          <p class="mt-0.5 text-xs text-amber-600">
            BROUILLON · PUBLIÉ · ANNULÉ · TERMINÉ + statuts d'affectation
          </p>
        </div>
      </label>

      <!-- Liste des ministères -->
      <div
        v-for="(min, mIdx) in setup.form.value.ministeres"
        :key="mIdx"
        class="rounded-xl border border-slate-200 bg-white shadow-sm"
      >
        <!-- En-tête ministère -->
        <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
          <span
            class="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-500"
          >
            {{ mIdx + 1 }}
          </span>
          <input
            v-model="min.nom"
            class="form-input flex-1"
            type="text"
            :placeholder="`Ministère ${mIdx + 1} — ex : Louange, Accueil…`"
            required
          />
          <button
            type="button"
            class="rounded-full p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
            title="Supprimer ce ministère"
            :disabled="setup.form.value.ministeres.length <= 1"
            @click="setup.removeMinistere(mIdx)"
          >
            <X class="size-4" />
          </button>
        </div>

        <div class="space-y-3 px-4 pt-3 pb-4">
          <!-- Init RBAC toggle -->
          <label class="flex cursor-pointer items-center gap-2">
            <input
              v-model="min.init_rbac"
              type="checkbox"
              class="size-3.5 rounded border-slate-300 accent-(--color-primary-600)"
            />
            <span class="flex items-center gap-1.5 text-xs text-slate-500">
              <ShieldCheck class="size-3.5 text-slate-400" />
              Initialiser les 4 rôles RBAC (Admin, Responsable, Membre, Super Admin)
            </span>
          </label>

          <!-- Catégories -->
          <div
            v-for="(cat, cIdx) in min.categories"
            :key="cIdx"
            class="space-y-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2.5"
          >
            <!-- En-tête catégorie -->
            <div class="flex items-center gap-2">
              <input
                v-model="cat.nom"
                class="form-input form-input-sm flex-1"
                type="text"
                :placeholder="`Catégorie — ex : Chant, Musiciens…`"
                required
              />
              <button
                type="button"
                class="rounded-full p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                title="Supprimer cette catégorie"
                @click="setup.removeCategorie(mIdx, cIdx)"
              >
                <X class="size-3.5" />
              </button>
            </div>

            <!-- Rôles compétence -->
            <div v-for="(role, rIdx) in cat.roles" :key="rIdx" class="flex items-center gap-1.5">
              <input
                v-model="role.code"
                class="form-input form-input-sm w-28 font-mono uppercase"
                type="text"
                placeholder="CODE"
                maxlength="20"
                required
              />
              <input
                v-model="role.libelle"
                class="form-input form-input-sm flex-1"
                type="text"
                placeholder="Libellé du rôle"
                required
              />
              <button
                type="button"
                class="rounded-full p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                @click="setup.removeRole(mIdx, cIdx, rIdx)"
              >
                <X class="size-3" />
              </button>
            </div>

            <button
              type="button"
              class="flex items-center gap-1 text-xs font-medium text-(--color-primary-600) transition-colors hover:text-(--color-primary-800)"
              @click="setup.addRole(mIdx, cIdx)"
            >
              <Plus class="size-3" />
              Compétence
            </button>
          </div>

          <button
            type="button"
            class="flex items-center gap-1.5 text-sm font-medium text-(--color-primary-600) transition-colors hover:text-(--color-primary-800)"
            @click="setup.addCategorie(mIdx)"
          >
            <Plus class="size-4" />
            Catégorie
          </button>
        </div>
      </div>

      <!-- Ajouter un ministère -->
      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-(--color-primary-200) py-3 text-sm font-medium text-(--color-primary-600) transition-colors hover:border-(--color-primary-400) hover:bg-(--color-primary-50)"
        @click="setup.addMinistere()"
      >
        <Plus class="size-4" />
        Ajouter un ministère
      </button>
    </form>

    <template #footer>
      <div class="flex justify-end gap-3">
        <button type="button" class="btn btn-secondary" @click="setup.close()">Annuler</button>
        <button
          type="submit"
          form="campus-setup-form"
          :disabled="setup.isSubmitting.value"
          class="btn btn-primary"
        >
          <Loader2 v-if="setup.isSubmitting.value" class="size-4 animate-spin" />
          <Zap v-else class="size-4" />
          Configurer
        </button>
      </div>
    </template>
  </AppDrawer>
</template>

<script setup lang="ts">
import { Loader2, Plus, ShieldCheck, X, Zap } from 'lucide-vue-next'
import { useCampusConfig } from '../../composables/useCampusConfig'
import { useCampusSetup } from '../../composables/useCampusSetup'

const campusConfig = useCampusConfig()
const setup = useCampusSetup()

async function handleSubmit(): Promise<void> {
  setup.isSubmitting.value = true
  try {
    await campusConfig.setupCampus(setup.form.value)
    setup.close()
  } catch {
    // Erreur déjà notifiée par l'intercepteur
  } finally {
    setup.isSubmitting.value = false
  }
}
</script>
