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
          <div class="form-group">
            <label>Utilisateur</label>
            <input v-model="modelValue.username" type="text" class="input-field" />
          </div>
          <div class="form-group">
            <label>Password</label>
            <div class="input-wrapper">
              <Lock class="input-icon" />
              <input v-model="modelValue.password" type="password" class="input-field with-icon" />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Rôles</label>
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
import type { UtilisateurWrite } from '~~/layers/base/types/utilisateur'

const props = defineProps<{ existingRoles?: string[] }>()
const modelValue = defineModel<UtilisateurWrite | undefined>()
const roleStore = useRoleStore()

onMounted(() => roleStore.fetchRoles())

// Pré-sélectionner les rôles existants dès que le model et le store sont prêts
watch(
  [() => modelValue.value, () => roleStore.items],
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

/* Conteneur de sécurité */
.security-box {
  @apply rounded-xl border border-slate-200 bg-slate-50/50 p-4 transition-all;
}

.security-content {
  @apply mt-2 border-t border-slate-200/60 pt-4;
}

/* Typographie & Formulaire */
.form-group {
  @apply flex flex-col gap-1.5;
}

.form-group label {
  @apply ml-0.5 text-[10px] font-bold text-slate-500 uppercase;
}

/* Inputs */
.input-field {
  @apply w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition-all outline-none hover:border-slate-300;
}

.input-field:focus {
  border-color: var(--color-primary-600);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary-600) 15%, transparent);
}

.input-wrapper {
  @apply relative flex items-center;
}

.input-icon {
  @apply pointer-events-none absolute left-3 size-3.5 text-slate-400;
}

.input-field.with-icon {
  @apply pl-9;
}

/* Role checkboxes */
.role-checkbox-label {
  @apply flex cursor-pointer items-center gap-1.5 text-sm text-slate-700;
}

/* Animation Expand */
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
