<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, BookOpen, Eye, EyeOff } from 'lucide-vue-next'
import { useSession } from '../stores/session'

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const router = useRouter()
const { login } = useSession()
async function submit() {
  error.value = ''; loading.value = true
  try { await login(username.value.trim(), password.value); await router.replace('/') }
  catch (e) { error.value = e instanceof Error ? e.message : '登录失败，请重试' }
  finally { loading.value = false }
}
</script>

<template>
  <main class="flex min-h-dvh flex-col px-6 pb-8 pt-[max(3rem,env(safe-area-inset-top))]">
    <div class="mb-12 flex items-center gap-3"><div class="grid h-11 w-11 place-items-center rounded-2xl bg-leaf-600 text-white shadow-soft"><BookOpen :size="23" /></div><div><p class="text-lg font-bold tracking-wide">拾光</p><p class="text-xs text-slate-500">每天 6 题，向目标靠近一点</p></div></div>
    <section class="flex-1">
      <p class="mb-2 text-sm font-semibold text-leaf-600">27 天暑期计划</p>
      <h1 class="text-[2rem] font-bold leading-tight tracking-tight">欢迎回来，<br />今天也一起认真学。</h1>
      <form class="mt-10 space-y-5" @submit.prevent="submit">
        <label class="block"><span class="mb-2 block text-sm font-medium">用户名或邮箱</span><input v-model="username" required autocomplete="username" class="h-14 w-full rounded-2xl border border-slate-200 bg-white/80 px-4 text-base shadow-sm placeholder:text-slate-300 focus:border-leaf-500 focus:outline-none" placeholder="输入你的账号" /></label>
        <label class="block"><span class="mb-2 block text-sm font-medium">密码</span><div class="relative"><input v-model="password" required :type="showPassword ? 'text' : 'password'" autocomplete="current-password" class="h-14 w-full rounded-2xl border border-slate-200 bg-white/80 px-4 pr-12 text-base shadow-sm placeholder:text-slate-300 focus:border-leaf-500 focus:outline-none" placeholder="输入密码" /><button type="button" class="absolute right-0 top-0 grid h-14 w-12 place-items-center text-slate-400" aria-label="显示或隐藏密码" @click="showPassword = !showPassword"><EyeOff v-if="showPassword" :size="20"/><Eye v-else :size="20"/></button></div></label>
        <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{{ error }}</p>
        <button :disabled="loading" class="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-ink font-semibold text-white shadow-soft transition active:scale-[.98] disabled:opacity-60">{{ loading ? '正在登录…' : '开始今日学习' }}<ArrowRight v-if="!loading" :size="19"/></button>
      </form>
    </section>
    <p class="mt-8 text-center text-xs leading-5 text-slate-400">保持自己的节奏。<br />每一次认真作答，都算数。</p>
  </main>
</template>
