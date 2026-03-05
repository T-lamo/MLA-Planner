<template>
  <section class="space-y-4">
    <!-- <header class="section-header">
      <User class="size-3.5" /><span>Informations Personnelles</span>
    </header> -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div class="form-group">
        <label>Nom</label>
        <input
          v-model="modelValue.nom"
          type="text"
          required
          class="input-field"
          placeholder="Ex: MARTIN"
        />
      </div>
      <div class="form-group">
        <label>Prénom</label>
        <input
          v-model="modelValue.prenom"
          type="text"
          required
          class="input-field"
          placeholder="Ex: Lucas"
        />
      </div>
      <div class="form-group">
        <label>Email</label>
        <div class="input-wrapper">
          <Mail class="input-icon" />
          <input v-model="modelValue.email" type="email" required class="input-field with-icon" />
        </div>
      </div>
      <div class="form-group">
        <label>Téléphone</label>
        <div class="input-wrapper">
          <Phone class="input-icon" />
          <input v-model="modelValue.telephone" type="tel" class="input-field with-icon" />
        </div>
      </div>
    </div>
    <div
      class="status-toggle-card group cursor-pointer"
      @click="modelValue.actif = !modelValue.actif"
    >
      <div class="flex flex-col">
        <span class="text-xs font-bold text-slate-700">Disponibilité</span>
        <span class="text-[11px] text-slate-500">Visible dans l'annuaire</span>
      </div>
      <button type="button" :class="['toggle-pill', modelValue.actif ? 'active' : '']">
        <span
          :class="['toggle-circle', modelValue.actif ? 'translate-x-5' : 'translate-x-0']"
        ></span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Mail, Phone } from 'lucide-vue-next'
import type { ProfilCreateFull } from '~~/layers/base/types/profiles'
const modelValue = defineModel<ProfilCreateFull>({ required: true })
</script>

<style scoped>
@reference "../../assets/css/main.css";
.section-header {
  @apply flex items-center gap-2 border-b border-slate-100 pb-1.5 text-[10px] font-black tracking-widest text-slate-400 uppercase;
}
.form-group {
  @apply flex flex-col gap-1.5;
}
.form-group label {
  @apply ml-0.5 text-[10px] font-bold text-slate-500 uppercase;
}
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
.status-toggle-card {
  @apply flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3.5;
}
.toggle-pill {
  @apply relative h-5 w-10 rounded-full bg-slate-200 transition-colors;
}
.toggle-pill.active {
  background-color: #10b981;
}
.toggle-circle {
  @apply absolute top-0.5 left-0.5 size-4 rounded-full bg-white shadow-md transition-transform duration-200;
}
</style>
