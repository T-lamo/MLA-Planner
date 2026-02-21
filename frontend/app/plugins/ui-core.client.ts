// frontend/plugins/ui-core.client.ts
export default defineNuxtPlugin(() => {
  if (import.meta.client) { // <--- Remplace process.client par ceci
    import('@shared/ui-core').then(() => {
      console.log('Composants chargés');
    });
  }
});