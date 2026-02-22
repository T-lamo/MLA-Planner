// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'
import eslintConfigPrettier from 'eslint-config-prettier'

export default withNuxt(
  {
    // Cibles : Typescript et Vue
    files: ['**/*.ts', '**/*.vue'],
    rules: {
      // Tes règles actuelles
      '@typescript-eslint/no-explicit-any': 'warn',
      'vue/multi-word-component-names': 'off',
      'vue/attribute-hyphenation': ['error', 'never'],
      'vue/no-deprecated-slot-attribute': 'off',
      
      // Ajout expert : Autorise les logs en dev, mais les bloque en prod
      'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    },
  },
  // On applique la configuration Prettier à la fin pour qu'elle ait la priorité
  eslintConfigPrettier,
).append({
  // On ignore les dossiers générés et les dépendances
  ignores: [
    '**/.nuxt/**',
    '**/.output/**',
    '**/dist/**',
    '**/node_modules/**',
    'public/**',
  ],
})