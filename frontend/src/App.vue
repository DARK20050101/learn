<script setup lang="ts">
import { onMounted } from 'vue'
import { useSession } from './stores/session'
const { restore } = useSession()
onMounted(restore)
</script>

<template>
  <div class="mx-auto min-h-dvh w-full max-w-lg">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in"><component :is="Component" /></transition>
    </router-view>
  </div>
</template>
