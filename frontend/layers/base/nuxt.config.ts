import { createResolver } from '@nuxt/kit'

const { resolve } = createResolver(import.meta.url)

export default defineNuxtConfig({
  // On résout le chemin de manière absolue au build
  css: [resolve('./app/assets/css/main.css')],
})
