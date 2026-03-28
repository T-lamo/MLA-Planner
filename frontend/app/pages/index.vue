<script setup lang="ts">
definePageMeta({
  middleware: [
    function () {
      return navigateTo('/planning/calendar', { replace: true })
    },
  ],
})
</script>
