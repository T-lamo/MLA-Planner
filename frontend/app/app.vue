<template>
  <div class="container">
    <ui-login 
      submitLabel="Accéder à mon compte"
      loadingLabel="Vérification..."
      identifierLabel="Identifiant"
      identifierPlaceholder="Ex: MLA-2024"
      passwordLabel="Mot de passe"
      :errorMessage="authError"
      @auth-submit="onLogin"
    >
      <div slot="logo" class="logo-wrapper">
        <!-- <img src="/img/logo-mla.png" alt="Logo" style="width: 80px;"> -->
        <h2>Espace Membre</h2>
      </div>
    </ui-login>
  </div>
</template>

<script setup>
import { ref } from 'vue';

// On déclare bien la variable réactive
const authError = ref("");

const onLogin = (event) => {
  // event.detail contient les données émises par Lit
  const { identifier, _password } = event.detail;
  console.log('Login attempt:', identifier);
  
  // Test simple
  if (identifier === "error") {
    authError.value = "Erreur de test détectée";
  } else {
    authError.value = "";
    alert(`Bienvenue ${identifier}`);
  }
};
</script>

<style scoped>
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  background-color: #f8fafc;
}

.logo-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

ui-login {
  --ui-primary: #10b981;
  --ui-radius: 12px;
}
</style>