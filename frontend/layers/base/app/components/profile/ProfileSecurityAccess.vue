<template>
  <section class="security-box">
    <div class="mb-4 flex items-center justify-between">
      <!-- <div class="flex items-center gap-2">
        <ShieldCheck class="size-4 text-slate-500" />
        <h4 class="text-[10px] font-black tracking-widest text-slate-700 uppercase">
          Accès Applicatif
        </h4>
      </div> -->
      <button type="button" class="text-primary-600 text-[11px] font-bold" @click="toggleAccess">
        {{ modelValue ? 'Révoquer' : 'Accorder' }}
      </button>
    </div>
    <Transition name="form-expand">
      <div
        v-if="modelValue"
        class="grid grid-cols-1 gap-4 border-t border-slate-200/60 pt-4 md:grid-cols-2"
      >
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
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { Lock } from 'lucide-vue-next'
import type { UtilisateurWrite } from '~~/layers/base/types/utilisateur'
const modelValue = defineModel<UtilisateurWrite | undefined>()
const toggleAccess = () => {
  if (modelValue.value) modelValue.value = undefined
  else modelValue.value = { username: '', password: '', actif: true, roles_ids: [] }
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
