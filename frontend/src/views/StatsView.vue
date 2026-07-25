<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowRight, CheckCircle2, Lightbulb, Target, TrendingUp } from 'lucide-vue-next'
import AppNav from '../components/AppNav.vue'
import LoadingState from '../components/LoadingState.vue'
import { api } from '../services/api'
import type { AnswerRecord, LearningReport } from '../types'

const loading = ref(true)
const error = ref('')
const report = ref<LearningReport | null>(null)
const records = ref<AnswerRecord[]>([])
const todayAccuracy = computed(() => Math.round((report.value?.today.accuracy ?? 0) * 100))
const weekAccuracy = computed(() => Math.round((report.value?.week.accuracy ?? 0) * 100))
const dayLabel = (value: string) =>
  new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', weekday: 'short' })
    .format(new Date(`${value}T12:00:00+08:00`))
    .replace('周', '')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [learningReport, answerPage] = await Promise.all([
      api.learningReport(),
      api.answers(),
    ])
    report.value = learningReport
    records.value = answerPage.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <main class="min-h-dvh px-5 pb-28 pt-[max(1.75rem,env(safe-area-inset-top))]">
    <header><p class="text-sm font-medium text-leaf-600">你的每一步都有记录</p><h1 class="mt-1 text-2xl font-bold">学习报告</h1></header>
    <LoadingState v-if="loading" />
    <div v-else-if="error" class="mt-10 rounded-2xl bg-red-50 p-5 text-sm text-red-600"><p>{{ error }}</p><button class="mt-4 min-h-11 rounded-xl bg-white px-4 font-semibold" @click="load">重新加载</button></div>
    <template v-else-if="report">
      <section class="mt-7 rounded-[2rem] bg-ink p-6 text-white shadow-soft">
        <div class="flex items-start justify-between"><div><p class="text-sm text-white/55">今日正确率</p><p class="mt-2 text-5xl font-bold tracking-tight">{{ todayAccuracy }}<span class="text-2xl text-white/60">%</span></p></div><span class="grid h-12 w-12 place-items-center rounded-2xl bg-white/10 text-[#dec481]"><Target :size="25"/></span></div>
        <div class="mt-7 h-2 overflow-hidden rounded-full bg-white/10"><div class="h-full rounded-full bg-[#dec481] transition-all" :style="{ width: `${todayAccuracy}%` }"/></div>
        <p class="mt-3 text-xs text-white/45">今日完成 {{ report.today.completed }} 题，答对 {{ report.today.correct }} 题</p>
      </section>

      <section class="mt-4 grid grid-cols-2 gap-3">
        <div class="rounded-2xl bg-white p-5 shadow-sm"><TrendingUp :size="21" class="text-leaf-600"/><p class="mt-4 text-2xl font-bold">{{ report.week.completed }}<span class="ml-1 text-sm font-normal text-slate-400">题</span></p><p class="mt-1 text-xs text-slate-500">本周完成</p></div>
        <div class="rounded-2xl bg-white p-5 shadow-sm"><CheckCircle2 :size="21" class="text-amber-500"/><p class="mt-4 text-2xl font-bold">{{ weekAccuracy }}<span class="ml-1 text-sm font-normal text-slate-400">%</span></p><p class="mt-1 text-xs text-slate-500">本周平均正确率</p></div>
      </section>

      <section class="mt-8">
        <div class="flex items-end justify-between"><h2 class="text-lg font-bold">近 7 天趋势</h2><span class="text-xs text-slate-400">按北京时间</span></div>
        <div class="mt-4 flex h-40 items-end justify-between rounded-2xl bg-white p-5 shadow-sm">
          <div v-for="day in report.recent_trend" :key="day.date" class="flex h-full flex-1 flex-col items-center justify-end gap-2">
            <div class="relative flex h-24 w-5 items-end overflow-hidden rounded-full bg-slate-100"><div class="w-full rounded-full bg-leaf-500 transition-all" :style="{ height: `${day.completed ? Math.max(18, day.accuracy * 100) : 0}%` }"/></div>
            <span class="text-[11px] text-slate-400">{{ dayLabel(day.date) }}</span>
          </div>
        </div>
      </section>

      <section class="mt-8">
        <h2 class="text-lg font-bold">薄弱知识点 TOP3</h2>
        <div v-if="!report.weak_points.length" class="mt-4 rounded-2xl bg-white p-8 text-center text-sm leading-6 text-slate-400">完成几次训练后，系统会在这里显示需要加强的知识点。</div>
        <div v-else class="mt-4 space-y-3">
          <div v-for="(point, index) in report.weak_points" :key="`${point.subject}-${point.knowledge_point_name}`" class="flex items-center gap-4 rounded-2xl bg-white p-4 shadow-sm">
            <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-red-50 font-bold text-coral">{{ index + 1 }}</span>
            <div class="min-w-0 flex-1"><p class="text-xs text-slate-400">{{ point.subject }}</p><p class="mt-1 truncate text-sm font-semibold">{{ point.knowledge_point_name }}</p><p class="mt-1 text-xs text-slate-400">练习 {{ point.attempt_count }} 次 · 错误 {{ point.error_count }} 次</p></div>
            <span class="text-sm font-bold text-slate-500">{{ Math.round(point.mastery_score) }}%</span>
          </div>
        </div>
      </section>

      <section class="mt-8 rounded-2xl bg-amber-50 p-5 text-amber-900">
        <div class="flex items-center gap-2 font-semibold"><Lightbulb :size="20"/>下一步建议</div>
        <p class="mt-3 text-sm leading-6 text-amber-800">{{ report.recommendation.message }}</p>
        <router-link v-if="report.recommendation.subject" to="/training/subject" class="mt-4 inline-flex min-h-11 items-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold">去专项训练<ArrowRight :size="16"/></router-link>
      </section>

      <section class="mt-8">
        <div class="flex items-center justify-between"><h2 class="text-lg font-bold">最近作答</h2><span class="text-xs text-slate-400">最近 20 题</span></div>
        <div v-if="!records.length" class="mt-4 rounded-2xl bg-white p-8 text-center text-sm text-slate-400">完成今日训练后，这里会出现学习记录。</div>
        <div v-else class="mt-4 space-y-3">
          <div v-for="record in records.slice(0, 8)" :key="record.id" class="flex items-center gap-3 rounded-2xl bg-white p-4 shadow-sm">
            <span class="grid h-9 w-9 place-items-center rounded-full" :class="record.is_correct ? 'bg-leaf-50 text-leaf-600' : 'bg-red-50 text-coral'"><CheckCircle2 v-if="record.is_correct" :size="19"/><span v-else class="text-lg font-bold">×</span></span>
            <div class="min-w-0 flex-1"><p class="text-sm font-medium">题目 #{{ record.question_id }}</p><p class="mt-1 truncate text-xs text-slate-400">你的答案：{{ Array.isArray(record.submitted_answer) ? record.submitted_answer.join('、') : record.submitted_answer }}</p></div>
            <time class="text-[11px] text-slate-400">{{ new Date(record.created_at).toLocaleDateString('zh-CN', {timeZone:'Asia/Shanghai', month:'numeric', day:'numeric'}) }}</time>
          </div>
        </div>
      </section>
    </template>
    <AppNav />
  </main>
</template>
