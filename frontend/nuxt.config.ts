// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/eslint'],

  // Configuration des variables d'environnement
  runtimeConfig: {
    public: {
      // Cette valeur sera remplacée par NUXT_PUBLIC_API_URL lors du build sur Netlify.
      // En local, elle utilisera l'adresse par défaut de ton FastAPI.
      apiBase: '' 
    }
  },
  vue: {
    compilerOptions: {
      // On dit à Vue de ne pas essayer de compiler les Web Components
      isCustomElement: (tag) => tag.startsWith('ui-')
    }
  }
})