export default defineNuxtConfig({
  // Ajoute ou complète la section imports
  imports: {
    dirs: [
      // Scanne tous les stores du layer auth
      'app/stores/**',
    ],
  },
})
