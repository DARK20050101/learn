<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, Brain, Check, Lightbulb, X } from 'lucide-vue-next'
import LoadingState from '../components/LoadingState.vue'
import RichText from '../components/RichText.vue'
import { api } from '../services/api'
import type { AIAnalysis, AnswerResult, AnswerValue, TrainingSession } from '../types'

const route = useRoute()
const router = useRouter()
const session = ref<TrainingSession | null>(null)
const answers = ref<Record<number, AnswerResult>>({})
const analyses = ref<Record<number, AIAnalysis | null>>({})
const selected = ref<string[]>([])
const textAnswer = ref('')
const boolAnswer = ref<boolean | null>(null)
const loading = ref(true)
const submitting = ref(false)
const aiLoading = ref(false)
const error = ref('')
const startedAt = ref(Date.now())
const sessionId = computed(() => Number(route.params.sessionId))
const position = computed(() => Math.max(1, Math.min(session.value?.total_questions ?? 1, Number(route.params.position) || 1)))
const item = computed(() => session.value?.items.find(value => value.position === position.value))
const result = computed(() => item.value ? answers.value[item.value.id] : undefined)
const analysis = computed(() => item.value ? analyses.value[item.value.id] : null)
const completed = computed(() => Object.keys(answers.value).length)
const canSubmit = computed(() => {
  const type = item.value?.question.question_type
  return type === 'true_false' ? boolAnswer.value !== null : (type === 'short_answer' || type === 'fill_blank') ? !!textAnswer.value.trim() : selected.value.length > 0
})
const nextPosition = computed(() => session.value?.items.find(value => !answers.value[value.id] && value.position !== position.value)?.position)

function toggle(option: string) {
  if (result.value) return
  if (item.value?.question.question_type === 'multiple_choice') {
    selected.value = selected.value.includes(option) ? selected.value.filter(value => value !== option) : [...selected.value, option]
  } else selected.value = [option]
}
function currentAnswer(): AnswerValue {
  const type = item.value!.question.question_type
  if (type === 'true_false') return boolAnswer.value!
  if (type === 'short_answer' || type === 'fill_blank') return textAnswer.value.trim()
  return type === 'multiple_choice' ? selected.value : selected.value[0]
}
function displayAnswer(value: AnswerValue) {
  if (Array.isArray(value)) return value.join('、')
  if (typeof value === 'boolean') return value ? '正确' : '错误'
  return value
}
function restoreInput() {
  selected.value = []; textAnswer.value = ''; boolAnswer.value = null
  if (!result.value) return
  const value = result.value.submitted_answer
  if (Array.isArray(value)) selected.value = [...value]
  else if (typeof value === 'boolean') boolAnswer.value = value
  else if (item.value?.question.question_type === 'short_answer' || item.value?.question.question_type === 'fill_blank') textAnswer.value = value
  else selected.value = [value]
}
async function pollAnalysis(answerId: number, itemId: number) {
  aiLoading.value = true
  try {
    for (let attempt = 0; attempt < 4; attempt++) {
      const response = await api.answerAnalysis(answerId)
      analyses.value[itemId] = response.analysis
      if (response.status !== 'pending') break
      await new Promise(resolve => window.setTimeout(resolve, 1200))
    }
  } catch {
    analyses.value[itemId] = null
  } finally {
    aiLoading.value = false
  }
}
async function submit() {
  if (!item.value || !canSubmit.value) return
  submitting.value = true; error.value = ''
  try {
    const response = await api.submitTrainingAnswer(item.value.id, {
      answer: currentAnswer(),
      duration_seconds: Math.round((Date.now() - startedAt.value) / 1000),
      idempotency_key: `training-${sessionId.value}-${item.value.id}`,
    })
    answers.value[item.value.id] = response
    if (!response.is_correct) await pollAnalysis(response.id, item.value.id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '答案提交失败，请重试'
  } finally {
    submitting.value = false
  }
}
async function next() {
  if (nextPosition.value) {
    await router.push(`/training/${sessionId.value}/${nextPosition.value}`)
    return
  }
  try {
    session.value = await api.completeTraining(sessionId.value)
    await router.push('/training/subject')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '训练暂时无法完成，请重试'
  }
}
async function load() {
  try {
    session.value = await api.trainingSession(sessionId.value)
    const restored = await api.trainingAnswers(sessionId.value)
    answers.value = Object.fromEntries(restored.filter(value => value.training_session_item_id).map(value => [value.training_session_item_id!, value]))
    restoreInput()
  } catch {
    await router.replace('/training/subject')
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(position, () => { restoreInput(); error.value = ''; startedAt.value = Date.now() })
watch(result, restoreInput)
</script>

<template>
  <main class="min-h-dvh px-5 pb-32 pt-[max(1.25rem,env(safe-area-inset-top))]">
    <LoadingState v-if="loading"/>
    <template v-else-if="session && item">
      <header><div class="flex items-center justify-between"><button class="grid h-11 w-11 place-items-center rounded-full bg-white shadow-sm" aria-label="退出训练" @click="router.push('/training/subject')"><ArrowLeft :size="20"/></button><div class="text-center"><p class="text-sm font-semibold">{{ session.title }}</p><p class="mt-1 text-xs text-slate-400">{{ completed }}/{{ session.total_questions }} 已完成</p></div><span class="w-11 text-right text-sm font-semibold">{{ position }}/{{ session.total_questions }}</span></div><div class="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100"><div class="h-full rounded-full bg-leaf-500 transition-all" :style="{ width: `${completed / session.total_questions * 100}%` }"/></div></header>
      <section class="mt-8"><div class="flex flex-wrap gap-2 text-xs font-semibold"><span class="rounded-full bg-leaf-50 px-3 py-1.5 text-leaf-700">{{ item.question.subject }}</span><span v-for="point in item.question.knowledge_points.slice(0, 2)" :key="point" class="rounded-full bg-slate-100 px-3 py-1.5 text-slate-500">{{ point }}</span></div><p class="mt-6 text-xs font-semibold text-slate-400">{{ item.question.title }} · 难度 {{ item.question.difficulty }}</p><h1 class="mt-3 text-xl font-semibold leading-8"><RichText :text="item.question.content" block/></h1></section>
      <section v-if="item.question.question_type === 'true_false'" class="mt-8 grid grid-cols-2 gap-3"><button v-for="choice in [{value:true,label:'正确'},{value:false,label:'错误'}]" :key="choice.label" :disabled="!!result" class="min-h-16 rounded-2xl border bg-white font-semibold" :class="boolAnswer === choice.value ? 'border-leaf-500 bg-leaf-50 text-leaf-700' : 'border-slate-200'" @click="boolAnswer = choice.value">{{ choice.label }}</button></section>
      <section v-else-if="item.question.question_type === 'short_answer'" class="mt-8"><textarea v-model="textAnswer" :disabled="!!result" rows="5" class="w-full rounded-2xl border border-slate-200 bg-white p-4 text-base leading-7 outline-none focus:border-leaf-500" placeholder="写下你的答案"/></section>
      <section v-else-if="item.question.question_type === 'fill_blank'" class="mt-8"><textarea v-model="textAnswer" :disabled="!!result" rows="4" class="w-full rounded-2xl border border-slate-200 bg-white p-4 text-base leading-7 outline-none focus:border-leaf-500" placeholder="输入填空处的答案"/></section>
      <section v-else class="mt-8 space-y-3"><button v-for="(option, index) in item.question.options" :key="option" :disabled="!!result" class="flex min-h-16 w-full items-center rounded-2xl border bg-white p-4 text-left text-sm leading-6" :class="selected.includes(option) ? 'border-leaf-500 bg-leaf-50 text-leaf-700' : 'border-slate-200'" @click="toggle(option)"><span class="mr-3 grid h-7 w-7 shrink-0 place-items-center rounded-full border text-xs font-semibold">{{ String.fromCharCode(65 + index) }}</span><RichText :text="option"/></button></section>
      <p v-if="error" class="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-600">{{ error }}</p>
      <section v-if="result" class="mt-8 overflow-hidden rounded-[1.75rem] bg-white shadow-soft"><div class="flex items-center gap-3 p-5" :class="result.is_correct ? 'bg-leaf-50 text-leaf-700' : 'bg-red-50 text-red-700'"><span class="grid h-10 w-10 place-items-center rounded-full text-white" :class="result.is_correct ? 'bg-leaf-600' : 'bg-coral'"><Check v-if="result.is_correct" :size="21"/><X v-else :size="21"/></span><div><h2 class="font-bold">{{ result.is_correct ? '回答正确' : '这道题再理一理' }}</h2><p class="mt-1 text-xs opacity-70">你的答案：{{ displayAnswer(result.submitted_answer) }} · 正确答案：{{ displayAnswer(result.correct_answer) }}</p></div></div><div v-if="result.explanation" class="border-b border-slate-100 p-5"><div class="mb-2 flex items-center gap-2 text-sm font-semibold"><Lightbulb :size="17" class="text-amber-500"/>标准解析</div><RichText :text="result.explanation" block class="text-sm leading-7 text-slate-600"/></div><div v-if="!result.is_correct" class="p-5"><div class="mb-3 flex items-center gap-2 text-sm font-semibold"><Brain :size="18" class="text-leaf-600"/>AI 学习分析</div><p v-if="aiLoading" class="text-sm text-slate-400">正在分析错误原因…</p><div v-else-if="analysis" class="space-y-3 text-sm leading-6"><span class="inline-block rounded-lg bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">{{ analysis.mistake_type }}</span><p>{{ analysis.reason }}</p><p class="text-leaf-700">建议：{{ analysis.suggestion }}</p></div><p v-else class="text-sm text-slate-400">AI 分析暂不可用，可先查看标准解析。</p></div></section>
      <div class="safe-bottom fixed inset-x-0 bottom-0 z-20 mx-auto max-w-lg border-t border-black/5 bg-paper/95 p-4 backdrop-blur-xl"><button v-if="!result" :disabled="!canSubmit || submitting" class="h-14 w-full rounded-2xl bg-ink font-semibold text-white disabled:bg-slate-200 disabled:text-slate-400" @click="submit">{{ submitting ? '正在提交…' : '提交答案' }}</button><button v-else class="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-leaf-600 font-semibold text-white" @click="next">{{ nextPosition ? '下一道未完成题' : '完成本次训练' }}<ArrowRight :size="19"/></button></div>
    </template>
  </main>
</template>
