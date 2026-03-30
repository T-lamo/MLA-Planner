<template>
  <li class="rounded-lg border border-slate-100 bg-slate-50">
    <!-- En-tête catégorie -->
    <div class="flex items-center gap-2 px-3 py-2">
      <button
        class="flex flex-1 items-center gap-2 text-left"
        type="button"
        @click="emit('toggle')"
      >
        <ChevronRight
          :class="[
            'size-3.5 shrink-0 text-slate-400 transition-transform duration-150',
            isOpen ? 'rotate-90' : '',
          ]"
        />
        <span class="text-sm font-medium text-slate-700">{{ categorie.libelle }}</span>
        <span
          class="rounded border border-slate-200 bg-white px-1.5 py-0.5 font-mono text-xs text-slate-500"
        >
          {{ categorie.code }}
        </span>
      </button>

      <button
        class="hover:bg-primary-50 hover:text-primary-600 rounded-full p-1 text-slate-400 transition-colors"
        title="Modifier la catégorie"
        type="button"
        @click.stop="emit('edit', ministereId, categorie.code)"
      >
        <Pencil class="size-3.5" />
      </button>

      <button
        class="rounded-full p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
        title="Supprimer la catégorie"
        type="button"
        @click.stop="handleDelete"
      >
        <X class="size-3.5" />
      </button>
    </div>

    <!-- Corps catégorie : rôles actifs en lecture seule -->
    <Transition name="expand">
      <div v-if="isOpen" class="border-t border-slate-100 px-3 pt-2 pb-3">
        <div v-if="activeRoles.length > 0" class="flex flex-wrap gap-1.5">
          <span
            v-for="role in activeRoles"
            :key="role.code"
            class="border-primary-100 bg-primary-50 text-primary-700 inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium"
          >
            {{ role.libelle }}
          </span>
        </div>
        <p v-else class="text-xs text-slate-400 italic">Aucun rôle actif configuré</p>
      </div>
    </Transition>
  </li>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChevronRight, Pencil, X } from 'lucide-vue-next'
import type { CampusSummaryCategorie } from '~~/layers/base/types/campus-config'
import type { RoleCompetenceRead } from '~~/layers/base/types/role-competence'
import { useMLAConfirm } from '../../composables/useMLAConfirm'

const props = defineProps<{
  categorie: CampusSummaryCategorie
  ministereId: string
  isOpen: boolean
}>()

const emit = defineEmits<{
  toggle: []
  delete: [ministereId: string, categorieId: string]
  edit: [ministereId: string, categorieId: string]
}>()

const { confirm } = useMLAConfirm()

const activeRoles = computed<RoleCompetenceRead[]>(() => props.categorie.roles_actifs ?? [])

async function handleDelete(): Promise<void> {
  const ok = await confirm(`Supprimer la catégorie "${props.categorie.libelle}" ?`)
  if (!ok) return
  emit('delete', props.ministereId, props.categorie.code)
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  max-height: 400px;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
