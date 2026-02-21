// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt({
  // Il manquait les accolades ici pour définir un objet
  rules: {
    '@typescript-eslint/no-explicit-any': 'warn',
    'vue/multi-word-component-names': 'off',
    "vue/attribute-hyphenation": ["error", "never"],
    "vue/no-deprecated-slot-attribute": "off"
  },
})