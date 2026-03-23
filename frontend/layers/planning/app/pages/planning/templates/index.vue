<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Copy, LayoutTemplate, Pencil, Trash2 } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { usePlanningTemplateStore } from '../../../stores/usePlanningTemplateStore'
import type { PlanningTemplateListItem } from '../../../types/planning.types'

const editingTemplateId = ref<string | null>(null)

definePageMeta({ middleware: [] })

const authStore = useAuthStore()
const templateStore = usePlanningTemplateStore()
const { templates, isLoading } = storeToRefs(templateStore)

const ministereFilter = ref<string | undefined>(undefined)
const deleteTarget = ref<string | null>(null)
const isDeleting = ref(false)

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

async function handleDuplicate(tpl: PlanningTemplateListItem) {
  await templateStore.duplicateTemplate(tpl.id)
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

const canWrite = computed(() => authStore.canManageChants)
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
      <table class="w-full text-sm">
        <thead
          class="border-b border-slate-100 bg-slate-50 text-xs font-semibold tracking-wider text-slate-500 uppercase"
        >
          <tr>
            <th class="px-4 py-3 text-left">Nom</th>
            <th class="px-4 py-3 text-left">Type activité</th>
            <th class="px-4 py-3 text-center">Créneaux</th>
            <th class="px-4 py-3 text-center">Utilisé</th>
            <th class="px-4 py-3 text-left">Dernière utilisation</th>
            <th class="px-4 py-3 text-left">Créé le</th>
            <th v-if="canWrite" class="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="tpl in templates" :key="tpl.id" class="transition-colors hover:bg-slate-50">
            <td class="px-4 py-3 font-medium text-slate-800">
              <div>{{ tpl.nom }}</div>
              <div v-if="tpl.description" class="mt-0.5 text-xs text-slate-400">
                {{ tpl.description }}
              </div>
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ tpl.activite_type ?? '—' }}
            </td>
            <td class="px-4 py-3 text-center text-slate-700">
              {{ tpl.nb_creneaux }}
            </td>
            <td class="px-4 py-3 text-center text-slate-700">{{ tpl.usage_count }}x</td>
            <td class="px-4 py-3 text-slate-500">
              {{ relativeDate(tpl.last_used_at) }}
            </td>
            <td class="px-4 py-3 text-slate-500">
              {{ formatDate(tpl.created_at) }}
            </td>
            <td v-if="canWrite" class="px-4 py-3">
              <div class="flex items-center justify-end gap-2">
                <button
                  class="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                  title="Modifier"
                  @click="editingTemplateId = tpl.id"
                >
                  <Pencil class="size-4" />
                </button>
                <button
                  class="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                  title="Dupliquer"
                  @click="handleDuplicate(tpl)"
                >
                  <Copy class="size-4" />
                </button>
                <button
                  class="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600"
                  title="Supprimer"
                  @click="openDeleteDialog(tpl.id)"
                >
                  <Trash2 class="size-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Drawer édition -->
    <TemplateEditDrawer
      :templateId="editingTemplateId"
      @close="editingTemplateId = null"
      @saved="templateStore.fetchTemplates(ministereFilter || undefined)"
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
              <button
                class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
                @click="cancelDelete"
              >
                Annuler
              </button>
              <button
                class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
                :disabled="isDeleting"
                @click="confirmDelete"
              >
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
