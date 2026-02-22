<script setup lang="ts">
// Redirige automatiquement vers la liste
definePageMeta({
  middleware: [
    function () {
      return navigateTo('/planning/list')
    },
  ],
})
</script>
