<script setup lang="ts">
defineProps<{ current: number; answered: number[] }>()
</script>
<template>
  <div class="flex items-center gap-2" aria-label="答题进度">
    <span v-for="n in 6" :key="n" class="h-2 rounded-full transition-all" :class="[n === current ? 'w-7 bg-leaf-600' : 'w-2', answered.includes(n) ? 'bg-leaf-500' : 'bg-slate-200']" />
  </div>
</template>
