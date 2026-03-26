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

        <div class="flex flex-col gap-1.5">
          <label class="ml-0.5 text-[10px] font-bold text-slate-500 uppercase">Rôles</label>
          <div v-if="roleStore.loading" class="text-[11px] text-slate-400">Chargement...</div>
          <div v-else class="flex flex-wrap gap-3">
            <label v-for="role in roleStore.items" :key="role.id" class="role-checkbox-label">
              <input
                type="checkbox"
                :value="role.id"
                :checked="modelValue.roles_ids?.includes(role.id)"
                class="accent-primary-600"
                @change="toggleRole(role.id)"
              />
              <span>{{ role.libelle }}</span>
            </label>
          </div>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { Lock } from 'lucide-vue-next'
import { useRoleStore } from '~~/layers/base/app/stores/useRoleStore'
import AppField from '../ui/AppField.vue'
import type { UtilisateurWrite } from '~~/layers/base/types/utilisateur'

const props = defineProps<{ existingRoles?: string[] }>()
const modelValue = defineModel<UtilisateurWrite | undefined>()
const roleStore = useRoleStore()

onMounted(() => roleStore.fetchRoles())

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

const toggleRole = (roleId: string) => {
  if (!modelValue.value) return
  const ids = modelValue.value.roles_ids ?? []
  if (ids.includes(roleId)) {
    modelValue.value.roles_ids = ids.filter((id) => id !== roleId)
  } else {
    modelValue.value.roles_ids = [...ids, roleId]
  }
}
</script>
<style scoped>
@reference "../../assets/css/main.css";

.security-box {
  @apply rounded-xl border border-slate-200 bg-slate-50/50 p-4 transition-all;
}

.role-checkbox-label {
  @apply flex cursor-pointer items-center gap-1.5 text-sm text-slate-700;
}

.form-expand-enter-active,
.form-expand-leave-active {
  transition: all 0.3s ease-in-out;
  max-height: 200px;
  overflow: hidden;
}

.form-expand-enter-from,
.form-expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}
</style>
