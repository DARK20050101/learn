<script setup lang="ts">
import { BarChart3, BookX, House } from 'lucide-vue-next'
</script>
<template>
  <nav class="safe-bottom fixed inset-x-0 bottom-0 z-30 mx-auto flex max-w-lg border-t border-black/5 bg-paper/95 px-5 pt-2 backdrop-blur-xl">
    <router-link to="/" class="flex flex-1 flex-col items-center gap-1 py-1 text-xs font-medium text-slate-400" active-class="!text-leaf-700"><House :size="22" stroke-width="1.8" />今日</router-link>
    <router-link to="/wrong-questions" class="flex flex-1 flex-col items-center gap-1 py-1 text-xs font-medium text-slate-400" active-class="!text-leaf-700"><BookX :size="22" stroke-width="1.8" />错题</router-link>
    <router-link to="/stats" class="flex flex-1 flex-col items-center gap-1 py-1 text-xs font-medium text-slate-400" active-class="!text-leaf-700"><BarChart3 :size="22" stroke-width="1.8" />记录</router-link>
  </nav>
</template>
