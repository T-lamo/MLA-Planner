<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, Loader2 } from 'lucide-vue-next'
import AppDrawer from '../AppDrawer.vue'
import AppField from '../ui/AppField.vue'
import { useRoleStore } from '~~/layers/base/app/stores/useRoleStore'

const props = defineProps<{
  isOpen: boolean
  mode: 'role' | 'capability'
}>()

const emit = defineEmits<{
  close: []
  created: [item: { id: string; label: string }]
}>()

const roleStore = useRoleStore()

const libelle = ref('')
const code = ref('')
const description = ref('')
const errorMsg = ref('')

const title = computed(() => (props.mode === 'role' ? 'Nouveau rôle' : 'Nouvelle capability'))

const isValid = computed(() => {
  if (props.mode === 'role') return libelle.value.trim().length > 0
  const v = code.value.trim().toUpperCase()
  return v.length > 0 && v.includes('_') && !v.includes(' ')
})

async function submit() {
  errorMsg.value = ''
  try {
    if (props.mode === 'role') {
      const created = await roleStore.createRole(libelle.value.trim())
      emit('created', { id: created.id, label: created.libelle ?? '' })
    } else {
      const created = await roleStore.createCapability(
        code.value.trim().toUpperCase(),
        description.value.trim() || undefined,
      )
      emit('created', { id: created.id, label: created.code })
    }
    resetForm()
    emit('close')
  } catch {
    errorMsg.value = 'Une erreur est survenue. Vérifiez les données saisies.'
  }
}

function resetForm() {
  libelle.value = ''
  code.value = ''
  description.value = ''
  errorMsg.value = ''
}

function handleClose() {
  resetForm()
  emit('close')
}
</script>

<template>
  <AppDrawer :isOpen="isOpen" :title="title" @close="handleClose">
    <div class="space-y-4 px-5 py-6">
      <!-- Mode rôle -->
      <template v-if="mode === 'role'">
        <AppField id="rd-libelle" label="Libellé" required>
          <input
            id="rd-libelle"
            v-model="libelle"
            type="text"
            class="form-input"
            placeholder="ex: Coordinateur Médias"
            @keyup.enter="isValid && submit()"
          />
        </AppField>
        <p class="text-[11px] text-slate-400">
          Le libellé est libre. Il sera visible lors de l'édition des profils utilisateurs.
        </p>
      </template>

      <!-- Mode capability -->
      <template v-else>
        <AppField id="rd-code" label="Code (RESOURCE_ACTION)" required>
          <input
            id="rd-code"
            v-model="code"
            type="text"
            class="form-input font-mono uppercase"
            placeholder="ex: MEDIA_WRITE"
            @keyup.enter="isValid && submit()"
          />
        </AppField>
        <AppField id="rd-desc" label="Description (optionnelle)">
          <input
            id="rd-desc"
            v-model="description"
            type="text"
            class="form-input"
            placeholder="ex: Permet de gérer les médias"
          />
        </AppField>
        <p class="text-[11px] text-slate-400">
          Convention obligatoire :
          <span class="font-mono font-semibold">RESSOURCE_ACTION</span>
          — majuscules, un underscore minimum, sans espace.
        </p>
      </template>

      <!-- Erreur -->
      <p v-if="errorMsg" class="text-xs text-red-500">{{ errorMsg }}</p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 transition-colors hover:bg-slate-50"
          @click="handleClose"
        >
          Annuler
        </button>
        <button
          type="button"
          :disabled="!isValid || roleStore.saving"
          class="bg-primary-600 hover:bg-primary-700 flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-50"
          @click="submit"
        >
          <Loader2 v-if="roleStore.saving" class="size-3.5 animate-spin" />
          <Check v-else class="size-3.5" />
          Créer
        </button>
      </div>
    </template>
  </AppDrawer>
</template>

<style scoped>
@reference "../../assets/css/main.css";
</style>
