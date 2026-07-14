<template>
  <div>{{ message }}</div>
</template>

<script setup>
import { ref } from "vue"
const message = ref("Hello")
</script>

<style scoped>
div { color: blue; }
</style>
