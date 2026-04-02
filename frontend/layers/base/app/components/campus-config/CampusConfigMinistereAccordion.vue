<template>
  <li class="rounded-xl border border-slate-200 bg-white shadow-sm">
    <!-- En-tête ministère -->
    <div class="flex items-center gap-2 px-4 py-3">
      <button
        class="flex flex-1 items-center gap-2 text-left"
        type="button"
        @click="emit('toggle')"
      >
        <ChevronRight
          :class="[
            'size-4 shrink-0 text-slate-400 transition-transform duration-200',
            isOpen ? 'rotate-90' : '',
          ]"
        />
        <span class="font-semibold text-slate-800">{{ ministere.nom }}</span>
        <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
          {{ ministere.categories.length }}
          {{ ministere.categories.length === 1 ? 'catégorie' : 'catégories' }}
        </span>
      </button>

      <button
        class="hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700 flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors"
        title="Modifier le ministère"
        type="button"
        @click.stop="emit('edit', ministere.id)"
      >
        <Pencil class="size-3.5" />
      </button>

      <button
        class="hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700 flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors"
        title="Gérer les rôles de ce ministère"
        type="button"
        @click.stop="isRoleManagerOpen = true"
      >
        <Settings class="size-3.5" />
        <span class="hidden sm:inline">Rôles</span>
      </button>

      <button
        class="hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700 flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors"
        title="Initialiser les 4 rôles RBAC standards"
        type="button"
        :disabled="isInitialisingRbac"
        @click.stop="handleInitRbac"
      >
        <Loader2 v-if="isInitialisingRbac" class="size-3.5 animate-spin" />
        <ShieldCheck v-else class="size-3.5" />
        <span class="hidden sm:inline">RBAC</span>
      </button>

      <button
        class="rounded-full p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
        title="Retirer le ministère du campus"
        type="button"
        @click.stop="handleRemove"
      >
        <X class="size-4" />
      </button>
    </div>

    <!-- Corps ministère -->
    <Transition name="expand">
      <div v-if="isOpen" class="border-t border-slate-100 px-4 pt-3 pb-4">
        <ul v-if="ministere.categories.length > 0" class="space-y-2">
          <CampusConfigCategorieAccordion
            v-for="cat in ministere.categories"
            :key="cat.code"
            :categorie="cat"
            :isOpen="openCategories.has(cat.code)"
            @toggle="toggleCategorie(cat.code)"
          />
        </ul>
        <p v-else class="py-2 text-sm text-slate-400 italic">Aucune catégorie définie</p>
      </div>
    </Transition>

    <!-- Modal gestion des rôles -->
    <CampusConfigRoleManagerModal
      :ministereId="ministere.id"
      :isOpen="isRoleManagerOpen"
      @close="isRoleManagerOpen = false"
    />
  </li>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ChevronRight, Loader2, Pencil, Settings, ShieldCheck, X } from 'lucide-vue-next'
import type { CampusSummaryMinistere } from '~~/layers/base/types/campus-config'
import { useCampusConfig } from '../../composables/useCampusConfig'
import { useMLAConfirm } from '../../composables/useMLAConfirm'

const props = defineProps<{
  ministere: CampusSummaryMinistere
  isOpen: boolean
}>()

const emit = defineEmits<{
  toggle: []
  remove: [ministereId: string]
  edit: [ministereId: string]
}>()

const campusConfig = useCampusConfig()
const { confirm } = useMLAConfirm()

const openCategories = ref(new Set<string>())
const isInitialisingRbac = ref(false)
const isRoleManagerOpen = ref(false)

function toggleCategorie(code: string): void {
  if (openCategories.value.has(code)) {
    openCategories.value.delete(code)
  } else {
    openCategories.value.add(code)
  }
}

async function handleRemove(): Promise<void> {
  const ok = await confirm(`Retirer "${props.ministere.nom}" du campus ?`)
  if (!ok) return
  emit('remove', props.ministere.id)
}

async function handleInitRbac(): Promise<void> {
  isInitialisingRbac.value = true
  try {
    await campusConfig.initRbac(props.ministere.id)
  } catch {
    // Erreur déjà notifiée par l'intercepteur
  } finally {
    isInitialisingRbac.value = false
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 800px;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
