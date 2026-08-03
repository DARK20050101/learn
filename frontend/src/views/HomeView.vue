<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, BookOpen, BookX, Check, LogOut, PenLine, RefreshCw, Sparkles, WifiOff, X } from 'lucide-vue-next'
import AppNav from '../components/AppNav.vue'
import LoadingState from '../components/LoadingState.vue'
import { ApiError, NetworkError, api } from '../services/api'
import { useSession } from '../stores/session'
import { useStudy } from '../stores/study'
import { chinaDateText, chinaGreeting } from '../utils/chinaTime'

type HomeStatus = 'generating' | 'ready' | 'insufficient_questions' | 'network_error' | 'server_error'
const status = ref<HomeStatus>('generating')
const error = ref('')
const refreshError = ref('')
const refreshing = ref(false)
const { state, resetStudy, restoreAnswers } = useStudy()
const { state: session, logout } = useSession()
const router = useRouter()
const completed = computed(() => state.task?.items.filter(i => !!state.answers[i.id]).length ?? 0)
const nextPosition = computed(() => state.task?.items.find(i => !state.answers[i.id])?.position ?? 6)
const taskCompleted = computed(() => completed.value === 6 && state.task?.status === 'completed')
const dateText = chinaDateText()
const greeting = chinaGreeting()

async function load() {
  status.value = 'generating'; error.value = ''; resetStudy()
  try {
    const task = await api.today()
    state.task = task
    restoreAnswers(await api.taskAnswers(task.id))
    status.value = 'ready'
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) status.value = 'insufficient_questions'
    else if (e instanceof NetworkError) status.value = 'network_error'
    else { status.value = 'server_error'; error.value = e instanceof Error ? e.message : '系统暂时无法加载' }
  }
}
async function refreshTask() {
  if (!state.task || refreshing.value) return
  if (!window.confirm('确认更换今天的 6 道题吗？每天只能更换一次。')) return
  refreshing.value = true
  refreshError.value = ''
  try {
    state.task = await api.refreshToday()
    restoreAnswers([])
  } catch (e) {
    refreshError.value = e instanceof Error ? e.message : '刷新失败，请稍后重试'
  } finally {
    refreshing.value = false
  }
}
function signOut() { logout(); router.replace('/login') }
onMounted(load)
</script>

<template>
  <main class="min-h-dvh px-5 pb-28 pt-[max(1.5rem,env(safe-area-inset-top))]">
    <header class="flex items-center justify-between"><div><p class="text-sm text-slate-500">{{ dateText }}</p><h1 class="mt-1 text-2xl font-bold">{{ greeting }}，{{ session.user?.username || '同学' }}</h1></div><button class="grid h-11 w-11 place-items-center rounded-full bg-white text-slate-500 shadow-sm" aria-label="退出登录" @click="signOut"><LogOut :size="19"/></button></header>
    <section v-if="status === 'generating'" class="mt-16 text-center"><LoadingState/><h2 class="mt-3 text-lg font-bold">正在准备今天的 6 道题</h2><p class="mt-2 text-sm text-slate-500">会根据你的学习情况自动选择，请稍等。</p></section>
    <section v-else-if="status === 'insufficient_questions'" class="mt-16 rounded-[2rem] bg-white p-8 text-center shadow-soft"><BookX class="mx-auto text-amber-500" :size="38"/><h2 class="mt-5 text-xl font-bold">今日题目暂时不足</h2><p class="mt-2 text-sm leading-6 text-slate-500">暂时无法准备完整的 6 道题，请联系测试负责人补充题库。你的学习记录不会受到影响。</p><button class="mt-6 inline-flex min-h-12 items-center gap-2 rounded-xl bg-leaf-50 px-5 py-3 text-sm font-semibold text-leaf-700" @click="load"><RefreshCw :size="17"/>重新加载</button></section>
    <section v-else-if="status === 'network_error'" class="mt-16 rounded-[2rem] bg-white p-8 text-center shadow-soft"><WifiOff class="mx-auto text-slate-400" :size="38"/><h2 class="mt-5 text-xl font-bold">网络连接失败</h2><p class="mt-2 text-sm leading-6 text-slate-500">请检查手机网络后重试，已经完成的学习记录不会丢失。</p><button class="mt-6 inline-flex min-h-12 items-center gap-2 rounded-xl bg-leaf-50 px-5 py-3 text-sm font-semibold text-leaf-700" @click="load"><RefreshCw :size="17"/>重新加载</button></section>
    <section v-else-if="status === 'server_error'" class="mt-16 rounded-2xl bg-red-50 p-5 text-sm text-red-600"><p class="font-semibold">系统暂时无法加载</p><p class="mt-2">{{ error }}</p><button class="mt-4 min-h-11 rounded-xl bg-white px-4 font-semibold" @click="load">稍后重试</button></section>
    <template v-else-if="state.task">
      <section class="relative mt-8 overflow-hidden rounded-[2rem] bg-ink p-6 text-white shadow-soft"><div class="absolute -right-10 -top-12 h-40 w-40 rounded-full border-[26px] border-white/5"/><div class="relative"><div class="flex items-center justify-between"><span class="rounded-full bg-white/10 px-3 py-1 text-xs font-medium">第 {{ state.task.day_number }} / 27 天</span><Sparkles :size="20" class="text-[#e9c985]"/></div><h2 class="mt-8 text-2xl font-bold">今日 6 题</h2><p class="mt-2 text-sm text-white/60">专注当下，不必着急。预计 20 分钟完成。</p><div class="mt-7 flex items-end justify-between"><div><span class="text-4xl font-bold">{{ completed }}</span><span class="ml-1 text-sm text-white/50">/ 6 已完成</span></div><span class="text-xs text-white/50">{{ Math.round(completed / 6 * 100) }}%</span></div><div class="mt-3 h-2 overflow-hidden rounded-full bg-white/10"><div class="h-full rounded-full bg-[#d6bd7d] transition-all duration-500" :style="{ width: `${completed / 6 * 100}%` }"/></div></div></section>
      <div v-if="completed === 0 && state.task.refresh_count === 0" class="mt-3 flex items-center justify-between px-1"><p class="text-xs text-slate-400">不适合？今天可更换一次</p><button class="inline-flex min-h-11 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-slate-600 disabled:opacity-50" :disabled="refreshing" @click="refreshTask"><RefreshCw :size="16" :class="{ 'animate-spin': refreshing }"/>{{ refreshing ? '正在更换' : '换一组题' }}</button></div>
      <p v-else-if="state.task.refresh_count === 1 && completed === 0" class="mt-3 px-1 text-xs text-slate-400">今日题目已更换</p>
      <div v-if="refreshError" class="mt-3 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{{ refreshError }}</div>
      <button v-if="completed < 6" class="mt-5 flex w-full items-center justify-between rounded-2xl bg-leaf-600 px-5 py-4 text-left text-white shadow-soft transition active:scale-[.98]" @click="router.push(`/question/${nextPosition}`)"><span><span class="block font-semibold">{{ completed ? '继续今日训练' : '开始今日训练' }}</span><span class="mt-0.5 block text-xs text-white/70">从第 {{ nextPosition }} 题开始</span></span><span class="grid h-10 w-10 place-items-center rounded-full bg-white/15"><ArrowRight :size="20"/></span></button>
      <div v-else class="mt-5 flex items-center gap-4 rounded-2xl p-5" :class="taskCompleted ? 'bg-leaf-50 text-leaf-700' : 'bg-amber-50 text-amber-700'"><span class="grid h-10 w-10 place-items-center rounded-full text-white" :class="taskCompleted ? 'bg-leaf-600' : 'bg-amber-500'"><Check :size="21"/></span><div><p class="font-semibold">{{ taskCompleted ? '今天的训练完成了' : '6 道题已作答' }}</p><p class="mt-1 text-xs opacity-80">{{ taskCompleted ? '辛苦了，记得看看学习记录' : '进入任意题目确认完成今日训练' }}</p></div></div>
      <section class="mt-8"><div class="mb-4 flex items-center justify-between"><h2 class="text-lg font-bold">题目一览</h2><span class="text-xs text-slate-400">已答题可查看结果</span></div><div class="space-y-3"><button v-for="item in state.task.items" :key="item.id" class="flex w-full items-center gap-4 rounded-2xl border border-black/[.04] bg-white/80 p-4 text-left shadow-sm" @click="router.push(`/question/${item.position}`)"><span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl font-semibold" :class="!state.answers[item.id] ? 'bg-slate-100 text-slate-500' : state.answers[item.id].is_correct ? 'bg-leaf-50 text-leaf-700' : 'bg-red-50 text-coral'"><Check v-if="state.answers[item.id]?.is_correct" :size="18"/><X v-else-if="state.answers[item.id]" :size="18"/><template v-else>{{ item.position }}</template></span><span class="min-w-0 flex-1"><span class="block text-xs text-slate-400">{{ item.question.subject }} · 难度 {{ item.question.difficulty }}</span><span class="mt-1 block truncate text-sm font-medium">{{ item.question.title }}</span><span class="mt-1 block text-xs" :class="!state.answers[item.id] ? 'text-slate-400' : state.answers[item.id].is_correct ? 'text-leaf-600' : 'text-coral'">{{ !state.answers[item.id] ? '继续作答' : state.answers[item.id].is_correct ? '回答正确 · 查看结果' : '回答错误 · 查看解析' }}</span></span><ArrowRight :size="17" class="text-slate-300"/></button></div></section>
    </template>
    <button v-if="status === 'ready'" class="mt-8 flex w-full items-center gap-4 rounded-2xl border border-black/[.04] bg-white p-5 text-left shadow-sm" @click="router.push('/training/subject')"><span class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-leaf-50 text-leaf-700"><BookOpen :size="22"/></span><span class="min-w-0 flex-1"><span class="block font-semibold">学科专项训练</span><span class="mt-1 block text-xs text-slate-400">按学科和知识点自主加练</span></span><ArrowRight :size="18" class="text-slate-300"/></button>
    <button v-if="status === 'ready'" class="mt-3 flex w-full items-center gap-4 rounded-2xl border border-black/[.04] bg-white p-5 text-left shadow-sm" @click="router.push('/training/fill')"><span class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-amber-50 text-amber-600"><PenLine :size="22"/></span><span class="min-w-0 flex-1"><span class="block font-semibold">概念记忆 · 知识填空</span><span class="mt-1 block text-xs text-slate-400">专门练习概念、定义与公式</span></span><ArrowRight :size="18" class="text-slate-300"/></button>
    <AppNav />
  </main>
</template>
