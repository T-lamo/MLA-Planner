<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { LayoutTemplate } from 'lucide-vue-next'
import AppTable from '~~/layers/base/app/components/ui/AppTable.vue'
import { usePlanningPermissions } from '../../../composables/usePlanningPermissions'
import { usePlanningTemplateStore } from '../../../stores/usePlanningTemplateStore'
import type {
  GenerateSeriesResponse,
  PlanningTemplateListItem,
  VisibiliteTemplate,
} from '../../../types/planning.types'

const editingTemplateId = ref<string | null>(null)

definePageMeta({ middleware: [] })

const { canWrite } = usePlanningPermissions()
const templateStore = usePlanningTemplateStore()
const { templates, isLoading } = storeToRefs(templateStore)

const ministereFilter = ref<string | undefined>(undefined)
const deleteTarget = ref<string | null>(null)
const isDeleting = ref(false)
const generateSerieTarget = ref<{ id: string; nom: string } | null>(null)

onMounted(() => templateStore.fetchTemplates())

watch(ministereFilter, (v) => templateStore.fetchTemplates(v || undefined))

function relativeDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86_400_000)
  if (diffDays === 0) return "Aujourd'hui"
  if (diffDays === 1) return 'Hier'
  if (diffDays < 7) return `Il y a ${diffDays} jours`
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

async function handleDuplicate(id: string) {
  await templateStore.duplicateTemplate(id)
}

function openDeleteDialog(id: string) {
  deleteTarget.value = id
}

function cancelDelete() {
  deleteTarget.value = null
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    await templateStore.deleteTemplate(deleteTarget.value)
    deleteTarget.value = null
  } finally {
    isDeleting.value = false
  }
}

function openGenerateSerie(tpl: PlanningTemplateListItem) {
  generateSerieTarget.value = { id: tpl.id, nom: tpl.nom }
}

function onSerieGenerated(_result: GenerateSeriesResponse) {
  generateSerieTarget.value = null
}

const columns = computed(() => [
  { key: 'nom', label: 'Nom' },
  { key: 'activite_type', label: 'Type activité' },
  { key: 'nb_creneaux', label: 'Créneaux', align: 'center' as const },
  { key: 'usage_count', label: 'Utilisé', align: 'center' as const },
  { key: 'visibilite', label: 'Visibilité' },
  { key: 'last_used_at', label: 'Dernière utilisation' },
  { key: 'created_at', label: 'Créé le' },
  ...(canWrite.value ? [{ key: 'actions', label: '', align: 'right' as const }] : []),
])

const VISIBILITE_LABELS: Record<VisibiliteTemplate, string> = {
  PRIVE: 'Privé',
  MINISTERE: 'Ministère',
  CAMPUS: 'Campus',
}
const VISIBILITE_CLASSES: Record<VisibiliteTemplate, string> = {
  PRIVE: 'bg-slate-100 text-slate-600',
  MINISTERE: 'bg-blue-50 text-blue-700',
  CAMPUS: 'bg-emerald-50 text-emerald-700',
}

function visibiliteBadge(v: VisibiliteTemplate) {
  return { label: VISIBILITE_LABELS[v] ?? v, cls: VISIBILITE_CLASSES[v] ?? '' }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <LayoutTemplate class="size-6 text-(--color-primary-700)" />
        <h1 class="text-xl font-bold text-slate-900">Bibliothèque de templates</h1>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="isLoading" class="space-y-3">
      <div v-for="n in 4" :key="n" class="h-14 animate-pulse rounded-lg bg-slate-100" />
    </div>

    <!-- État vide -->
    <div
      v-else-if="!isLoading && templates.length === 0"
      class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center"
    >
      <LayoutTemplate class="mb-4 size-12 text-slate-300" />
      <p class="text-base font-medium text-slate-600">Aucun template disponible</p>
      <p class="mt-1 text-sm text-slate-400">
        Sauvegardez un planning comme template pour commencer.
      </p>
      <NuxtLink
        to="/planning/list"
        class="mt-4 text-sm font-medium text-(--color-primary-700) hover:underline"
      >
        Aller aux plannings
      </NuxtLink>
    </div>

    <!-- Table -->
    <div v-else class="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <AppTable
        :columns="columns"
        :rows="templates as Record<string, unknown>[]"
        emptyLabel="Aucun template disponible"
      >
        <template #cell-nom="{ row }">
          <div class="font-medium text-slate-800">
            {{ (row as unknown as PlanningTemplateListItem).nom }}
          </div>
          <div
            v-if="(row as unknown as PlanningTemplateListItem).description"
            class="mt-0.5 text-xs text-slate-400"
          >
            {{ (row as unknown as PlanningTemplateListItem).description }}
          </div>
        </template>

        <template #cell-activite_type="{ value }">
          <span class="text-slate-600">{{ (value as string | null) ?? '—' }}</span>
        </template>

        <template #cell-nb_creneaux="{ value }">
          <span class="text-slate-700">{{ value as number }}</span>
        </template>

        <template #cell-usage_count="{ value }">
          <span class="text-slate-700">{{ value as number }}x</span>
        </template>

        <template #cell-visibilite="{ row }">
          <span
            :class="visibiliteBadge((row as unknown as PlanningTemplateListItem).visibilite).cls"
            class="rounded-full px-2 py-0.5 text-xs font-medium"
          >
            {{ visibiliteBadge((row as unknown as PlanningTemplateListItem).visibilite).label }}
          </span>
        </template>

        <template #cell-last_used_at="{ row }">
          <span class="text-slate-500">{{
            relativeDate((row as unknown as PlanningTemplateListItem).last_used_at)
          }}</span>
        </template>

        <template #cell-created_at="{ row }">
          <span class="text-slate-500">{{
            formatDate((row as unknown as PlanningTemplateListItem).created_at)
          }}</span>
        </template>

        <template v-if="canWrite" #cell-actions="{ row }">
          <TemplateActionMenu
            :template="row as unknown as PlanningTemplateListItem"
            @edit="editingTemplateId = (row as unknown as PlanningTemplateListItem).id"
            @duplicate="handleDuplicate((row as unknown as PlanningTemplateListItem).id)"
            @generate-serie="openGenerateSerie(row as unknown as PlanningTemplateListItem)"
            @delete="openDeleteDialog((row as unknown as PlanningTemplateListItem).id)"
          />
        </template>
      </AppTable>
    </div>

    <!-- Drawer édition -->
    <TemplateEditDrawer
      :templateId="editingTemplateId"
      @close="editingTemplateId = null"
      @saved="templateStore.fetchTemplates(ministereFilter || undefined)"
    />

    <!-- Drawer génération de série -->
    <GenerateSerieDrawer
      :templateId="generateSerieTarget?.id ?? null"
      :templateNom="generateSerieTarget?.nom ?? ''"
      @close="generateSerieTarget = null"
      @generated="onSerieGenerated"
    />

    <!-- Dialog suppression -->
    <Teleport to="body">
      <transition name="dialog-fade">
        <div
          v-if="deleteTarget"
          class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4"
        >
          <div class="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
            <h2 class="text-base font-semibold text-slate-900">Supprimer ce template ?</h2>
            <p class="mt-2 text-sm text-slate-500">
              Les plannings créés depuis ce template ne seront pas affectés. Cette action est
              irréversible.
            </p>
            <div class="mt-6 flex justify-end gap-3">
              <button class="btn btn-secondary" @click="cancelDelete">Annuler</button>
              <button class="btn btn-danger" :disabled="isDeleting" @click="confirmDelete">
                {{ isDeleting ? 'Suppression…' : 'Supprimer' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
@reference "~~/layers/base/app/assets/css/main.css";

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}
.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}
</style>
