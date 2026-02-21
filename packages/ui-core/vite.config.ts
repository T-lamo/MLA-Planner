import { defineConfig } from 'vite';
import dts from 'vite-plugin-dts';
import { resolve } from 'path';

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'UiCore',
      fileName: 'ui-core',
      formats: ['es'] // Bundle ESM unique pour une portabilité moderne
    },
    rollupOptions: {
      external: [/^lit/], // Ne pas inclure Lit dans le bundle final
      output: {
        globals: { lit: 'Lit' }
      }
    },
    minify: 'terser'
  },
  plugins: [dts({ insertTypesEntry: true })]
});