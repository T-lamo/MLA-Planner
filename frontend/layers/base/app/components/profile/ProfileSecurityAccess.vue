<template>
  <section class="security-box">
    <div class="mb-4 flex items-center justify-between">
      <button type="button" class="text-primary-600 text-[11px] font-bold" @click="toggleAccess">
        {{ modelValue ? 'Révoquer' : 'Accorder' }}
      </button>
    </div>
    <Transition name="form-expand">
      <div v-if="modelValue" class="space-y-4 border-t border-slate-200/60 pt-4">
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <AppField id="psa-username" label="Utilisateur">
            <input id="psa-username" v-model="modelValue.username" type="text" class="form-input" />
          </AppField>
          <AppField id="psa-password" label="Password">
            <template #leading-icon>
              <Lock class="size-3.5" />
            </template>
            <input
              id="psa-password"
              v-model="modelValue.password"
              type="password"
              class="form-input has-leading-icon"
            />
          </AppField>
        </div>

        <AppField id="psa-roles" label="Rôles">
          <div v-if="roleStore.loading" class="text-[11px] text-slate-400">Chargement…</div>
          <AppMultiSelect
            v-else
            :modelValue="modelValue.roles_ids ?? []"
            :options="roleOptions"
            placeholder="Assigner des rôles…"
            @update:model-value="modelValue.roles_ids = $event"
          />
        </AppField>
      </div>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { Lock } from 'lucide-vue-next'
import { useRoleStore } from '~~/layers/base/app/stores/useRoleStore'
import AppField from '../ui/AppField.vue'
import AppMultiSelect from '../ui/AppMultiSelect.vue'
import type { UtilisateurWrite } from '~~/layers/base/types/utilisateur'

const props = defineProps<{ existingRoles?: string[] }>()
const modelValue = defineModel<UtilisateurWrite | undefined>()
const roleStore = useRoleStore()

onMounted(() => roleStore.fetchRoles())

const roleOptions = computed(() => roleStore.items.map((r) => ({ label: r.libelle, value: r.id })))

// Pré-sélectionner les rôles existants dès que le model et le store sont prêts
watch(
  [() => modelValue.value, () => roleStore.items, () => props.existingRoles],
  ([val, items]) => {
    if (!val || val.roles_ids?.length || !items.length || !props.existingRoles?.length) return
    val.roles_ids = items.filter((r) => props.existingRoles!.includes(r.libelle)).map((r) => r.id)
  },
  { immediate: true },
)

const toggleAccess = () => {
  if (modelValue.value) {
    modelValue.value = undefined
  } else {
    const preselected = roleStore.items
      .filter((r) => props.existingRoles?.includes(r.libelle))
      .map((r) => r.id)
    modelValue.value = { username: '', password: '', actif: true, roles_ids: preselected }
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.security-box {
  @apply rounded-xl border border-slate-200 bg-slate-50/50 p-4 transition-all;
}

.form-expand-enter-active,
.form-expand-leave-active {
  transition: all 0.3s ease-in-out;
  max-height: 300px;
  overflow: hidden;
}

.form-expand-enter-from,
.form-expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}
</style>
