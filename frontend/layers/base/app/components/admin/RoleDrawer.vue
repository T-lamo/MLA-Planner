<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, Loader2 } from 'lucide-vue-next'
import AppDrawer from '../AppDrawer.vue'
import AppField from '../ui/AppField.vue'
import { useRoleStore } from '~~/layers/base/app/stores/useRoleStore'

defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
  created: [item: { id: string; label: string }]
}>()

const roleStore = useRoleStore()

const libelle = ref('')
const errorMsg = ref('')

const isValid = computed(() => libelle.value.trim().length > 0)

async function submit() {
  errorMsg.value = ''
  try {
    const created = await roleStore.createRole(libelle.value.trim())
    emit('created', { id: created.id, label: created.libelle ?? '' })
    resetForm()
    emit('close')
  } catch {
    errorMsg.value = 'Une erreur est survenue. Vérifiez les données saisies.'
  }
}

function resetForm() {
  libelle.value = ''
  errorMsg.value = ''
}

function handleClose() {
  resetForm()
  emit('close')
}
</script>

<template>
  <AppDrawer :isOpen="isOpen" title="Nouveau rôle" @close="handleClose">
    <div class="space-y-4 px-5 py-6">
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
