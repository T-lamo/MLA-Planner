<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50">
    <ui-login
      submitLabel="Accéder à mon compte"
      loadingLabel="Vérification..."
      identifierLabel="Identifiant"
      identifierPlaceholder="Ex: MLA-2024"
      passwordLabel="Mot de passe"
      :errorMessage="authError"
      @auth-submit="onLogin"
    >
      <div slot="logo" class="flex flex-col items-center gap-4">
        <h2 class="text-xl font-bold text-slate-800">Espace Membre</h2>
      </div>
    </ui-login>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const authError = ref('')

const onLogin = (event) => {
  const { _identifier, _password } = event.detail
  // console.log('Tentative de connexion dans le layer Auth:', identifier)
  // Logique d'appel API FastAPI ici
}
</script>

<style scoped>
/* On peut personnaliser le Web Component via ses CSS Variables ici */
ui-login {
  --ui-primary: #2563eb; /* Blue-600 */
  --ui-radius: 12px;
}
</style>
