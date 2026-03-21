<script setup lang="ts">
import { ChevronRight, GripVertical, Pencil, Plus, Save, Trash2, X } from 'lucide-vue-next'
import { useAuthStore } from '~~/layers/auth/app/stores/useAuthStore'
import { useUIStore } from '~~/layers/base/app/stores/useUiStore'
import type { ChantCategorieRead } from '../../types/chant'

definePageMeta({
  middleware: [
    function () {
      const auth = useAuthStore()
      if (!auth.canManageChants) return navigateTo('/songbook', { replace: true })
    },
  ],
})

const {
  categories,
  chants,
  loadCategories,
  loadChants,
  createCategorie,
  updateCategorie,
  deleteCategorie,
} = useSongbook()

const uiStore = useUIStore()
const campusId = computed(() => uiStore.selectedCampusId ?? '')

// ── Comptage des chants par catégorie ──────────────────────────────────────
const chantsParCategorie = computed(() => {
  const map: Record<string, number> = {}
  for (const c of chants.value) {
    if (c.categorie_code) {
      map[c.categorie_code] = (map[c.categorie_code] ?? 0) + 1
    }
  }
  return map
})

// ── Formulaire — nouvelle catégorie ───────────────────────────────────────
const newForm = reactive({ code: '', libelle: '', ordre: '' })
const newErrors = reactive({ code: '', libelle: '' })
const isCreating = ref(false)

async function handleCreate() {
  newErrors.code = ''
  newErrors.libelle = ''

  const code = newForm.code.trim().toUpperCase().replace(/\s+/g, '_')
  const libelle = newForm.libelle.trim()

  if (!code) {
    newErrors.code = 'Code requis'
    return
  }
  if (!libelle) {
    newErrors.libelle = 'Libellé requis'
    return
  }
  if (categories.value.some((c) => c.code === code)) {
    newErrors.code = 'Ce code existe déjà'
    return
  }

  isCreating.value = true
  try {
    await createCategorie({
      code,
      libelle,
      ordre: newForm.ordre ? Number(newForm.ordre) : undefined,
    })
    newForm.code = ''
    newForm.libelle = ''
    newForm.ordre = ''
  } finally {
    isCreating.value = false
  }
}

// ── Édition inline ─────────────────────────────────────────────────────────
const editingCode = ref<string | null>(null)
const editForm = reactive({ libelle: '', ordre: '' })
const isSavingEdit = ref(false)

function startEdit(cat: ChantCategorieRead) {
  editingCode.value = cat.code
  editForm.libelle = cat.libelle
  editForm.ordre = String(cat.ordre)
}

function cancelEdit() {
  editingCode.value = null
}

async function handleUpdate(code: string) {
  const libelle = editForm.libelle.trim()
  if (!libelle) return

  isSavingEdit.value = true
  try {
    await updateCategorie(code, {
      libelle,
      ordre: editForm.ordre ? Number(editForm.ordre) : undefined,
    })
    editingCode.value = null
  } finally {
    isSavingEdit.value = false
  }
}

// ── Suppression ────────────────────────────────────────────────────────────
const isDeletingCode = ref<string | null>(null)

async function handleDelete(cat: ChantCategorieRead) {
  const count = chantsParCategorie.value[cat.code] ?? 0
  const msg =
    count > 0
      ? `Cette catégorie contient ${count} chant(s). Supprimer quand même « ${cat.libelle} » ?`
      : `Supprimer la catégorie « ${cat.libelle} » ?`
  if (!confirm(msg)) return

  isDeletingCode.value = cat.code
  try {
    await deleteCategorie(cat.code)
  } finally {
    isDeletingCode.value = null
  }
}

onMounted(async () => {
  await Promise.all([
    categories.value.length === 0 ? loadCategories() : Promise.resolve(),
    chants.value.length === 0 ? loadChants(campusId.value) : Promise.resolve(),
  ])
})
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-8">
    <!-- ── Breadcrumb ──────────────────────────────────────────────────── -->
    <nav class="mb-6 flex items-center gap-1.5 text-sm text-(--color-neutral-500)">
      <NuxtLink to="/songbook" class="hover:text-(--color-neutral-700)">Répertoire</NuxtLink>
      <ChevronRight class="h-3.5 w-3.5 shrink-0" />
      <span class="text-(--color-neutral-800)">Catégories</span>
    </nav>

    <!-- ── Titre ──────────────────────────────────────────────────────── -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-(--color-neutral-900)">Catégories de chants</h1>
      <p class="mt-1 text-sm text-(--color-neutral-500)">
        Gérez les catégories utilisées pour classer le répertoire.
      </p>
    </div>

    <!-- ── Formulaire — nouvelle catégorie ───────────────────────────── -->
    <div class="mb-8 rounded-2xl border border-(--color-neutral-200) bg-white p-6">
      <p class="mb-4 text-sm font-semibold text-(--color-neutral-700)">Ajouter une catégorie</p>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_2fr_auto_auto]">
        <!-- Code -->
        <div>
          <input
            v-model="newForm.code"
            type="text"
            placeholder="Code (ex : LOUANGE)"
            class="w-full rounded-lg border px-3 py-2 text-sm uppercase focus:outline-none"
            :class="
              newErrors.code
                ? 'border-(--color-red-400) focus:border-(--color-red-400)'
                : 'border-(--color-neutral-300) focus:border-(--color-primary-400)'
            "
            @keyup.enter="handleCreate"
          />
          <p v-if="newErrors.code" class="mt-0.5 text-xs text-(--color-red-500)">
            {{ newErrors.code }}
          </p>
        </div>
        <!-- Libellé -->
        <div>
          <input
            v-model="newForm.libelle"
            type="text"
            placeholder="Libellé (ex : Louange)"
            class="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none"
            :class="
              newErrors.libelle
                ? 'border-(--color-red-400) focus:border-(--color-red-400)'
                : 'border-(--color-neutral-300) focus:border-(--color-primary-400)'
            "
            @keyup.enter="handleCreate"
          />
          <p v-if="newErrors.libelle" class="mt-0.5 text-xs text-(--color-red-500)">
            {{ newErrors.libelle }}
          </p>
        </div>
        <!-- Ordre -->
        <input
          v-model="newForm.ordre"
          type="number"
          min="0"
          placeholder="Ordre"
          class="w-24 rounded-lg border border-(--color-neutral-300) px-3 py-2 text-sm focus:border-(--color-primary-400) focus:outline-none"
          @keyup.enter="handleCreate"
        />
        <!-- Bouton -->
        <button
          type="button"
          :disabled="isCreating"
          class="inline-flex items-center gap-1.5 rounded-lg bg-(--color-primary-600) px-4 py-2 text-sm font-medium text-white hover:bg-(--color-primary-700) disabled:opacity-50"
          @click="handleCreate"
        >
          <Plus class="h-4 w-4" />
          Ajouter
        </button>
      </div>
    </div>

    <!-- ── Liste des catégories ───────────────────────────────────────── -->
    <div class="rounded-2xl border border-(--color-neutral-200) bg-white">
      <div
        v-if="categories.length === 0"
        class="py-12 text-center text-sm text-(--color-neutral-400)"
      >
        Aucune catégorie pour l'instant.
      </div>

      <ul v-else class="divide-y divide-(--color-neutral-100)">
        <li
          v-for="cat in [...categories].sort((a, b) => a.ordre - b.ordre)"
          :key="cat.code"
          class="flex items-center gap-3 px-5 py-4"
        >
          <!-- Poignée (décorative) -->
          <GripVertical class="h-4 w-4 shrink-0 text-(--color-neutral-300)" />

          <!-- Mode lecture -->
          <template v-if="editingCode !== cat.code">
            <div class="min-w-0 flex-1">
              <span
                class="inline-block rounded-full bg-(--color-primary-100) px-2.5 py-0.5 font-mono text-xs font-medium text-(--color-primary-700)"
              >
                {{ cat.code }}
              </span>
              <span class="ml-2 text-sm font-medium text-(--color-neutral-800)">{{
                cat.libelle
              }}</span>
            </div>
            <span class="text-xs text-(--color-neutral-400)">
              {{ chantsParCategorie[cat.code] ?? 0 }} chant(s) · ordre {{ cat.ordre }}
            </span>
            <div class="flex shrink-0 items-center gap-1">
              <button
                type="button"
                class="rounded-lg p-1.5 text-(--color-neutral-400) hover:bg-(--color-neutral-100) hover:text-(--color-neutral-600)"
                title="Modifier"
                @click="startEdit(cat)"
              >
                <Pencil class="h-4 w-4" />
              </button>
              <button
                type="button"
                :disabled="isDeletingCode === cat.code"
                class="rounded-lg p-1.5 text-(--color-neutral-400) hover:bg-(--color-red-50) hover:text-(--color-red-600) disabled:opacity-50"
                title="Supprimer"
                @click="handleDelete(cat)"
              >
                <Trash2 class="h-4 w-4" />
              </button>
            </div>
          </template>

          <!-- Mode édition inline -->
          <template v-else>
            <div class="flex flex-1 items-center gap-2">
              <span
                class="rounded-full bg-(--color-neutral-100) px-2.5 py-0.5 font-mono text-xs font-medium text-(--color-neutral-500)"
              >
                {{ cat.code }}
              </span>
              <input
                v-model="editForm.libelle"
                type="text"
                class="flex-1 rounded-lg border border-(--color-primary-400) px-3 py-1.5 text-sm focus:outline-none"
                @keyup.enter="handleUpdate(cat.code)"
                @keyup.escape="cancelEdit"
              />
              <input
                v-model="editForm.ordre"
                type="number"
                min="0"
                class="w-20 rounded-lg border border-(--color-neutral-300) px-3 py-1.5 text-sm focus:border-(--color-primary-400) focus:outline-none"
                @keyup.enter="handleUpdate(cat.code)"
                @keyup.escape="cancelEdit"
              />
            </div>
            <div class="flex shrink-0 items-center gap-1">
              <button
                type="button"
                :disabled="isSavingEdit"
                class="rounded-lg p-1.5 text-(--color-primary-600) hover:bg-(--color-primary-50) disabled:opacity-50"
                title="Enregistrer"
                @click="handleUpdate(cat.code)"
              >
                <Save class="h-4 w-4" />
              </button>
              <button
                type="button"
                class="rounded-lg p-1.5 text-(--color-neutral-400) hover:bg-(--color-neutral-100) hover:text-(--color-neutral-600)"
                title="Annuler"
                @click="cancelEdit"
              >
                <X class="h-4 w-4" />
              </button>
            </div>
          </template>
        </li>
      </ul>
    </div>
  </div>
</template>
