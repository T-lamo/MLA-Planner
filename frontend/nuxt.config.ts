// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite'
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/eslint', '@pinia/nuxt'],

  // Configuration des variables d'environnement
  runtimeConfig: {
    public: {
      // Cette valeur sera remplacée par NUXT_PUBLIC_API_URL lors du build sur Netlify.
      // En local, elle utilisera l'adresse par défaut de ton FastAPI.
      apiBase: '',
    },
  },
  vue: {
    compilerOptions: {
      // On dit à Vue de ne pas essayer de compiler les Web Components
      isCustomElement: (tag) => tag.startsWith('ui-'),
    },
  },

  // Activation explicite du mode Nuxt 4
  future: {
    compatibilityVersion: 4,
  },

  extends: ['./layers/base', './layers/auth', './layers/planning'],

  vite: {
    plugins: [
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      tailwindcss() as any,
    ],
  },

  // Neutralisation de PostCSS pour éviter l'erreur ENOENT tailwindcss
  postcss: {
    plugins: {
      autoprefixer: {},
    },
  },

  // Désactivation du scan auto de tailwind module s'il est présent par erreur ailleurs
  features: {
    inlineStyles: false,
  },
})
