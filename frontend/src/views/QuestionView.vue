<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, Brain, Check, Lightbulb, X } from 'lucide-vue-next'
import LoadingState from '../components/LoadingState.vue'
import ProgressDots from '../components/ProgressDots.vue'
import RichText from '../components/RichText.vue'
import { api } from '../services/api'
import { useStudy } from '../stores/study'
import type { AIAnalysis, AnswerValue, DifficultyFeedback } from '../types'

const route = useRoute(); const router = useRouter(); const { state, restoreAnswers } = useStudy()
const loading = ref(!state.task); const submitting = ref(false); const completing = ref(false); const aiLoading = ref(false); const error = ref('')
const feedbackSaving = ref(false); const feedbackError = ref('')
const selected = ref<string[]>([]); const textAnswer = ref(''); const boolAnswer = ref<boolean | null>(null)
const startedAt = ref(Date.now())
const position = computed(() => Math.min(6, Math.max(1, Number(route.params.position) || 1)))
const item = computed(() => state.task?.items.find(i => i.position === position.value))
const result = computed(() => item.value ? state.answers[item.value.id] : undefined)
const analysisResponse = computed(() => item.value ? state.analyses[item.value.id] : undefined)
const analysis = computed<AIAnalysis | undefined>(() => analysisResponse.value?.analysis ?? undefined)
const answeredPositions = computed(() => state.task?.items.filter(i => state.answers[i.id]).map(i => i.position) ?? [])
const nextUnansweredPosition = computed(() => {
  const items = state.task?.items ?? []
  return items.find(i => i.position > position.value && !state.answers[i.id])?.position
    ?? items.find(i => !state.answers[i.id])?.position
})
const canSubmit = computed(() => { const t = item.value?.question.question_type; return t === 'true_false' ? boolAnswer.value !== null : t === 'short_answer' ? !!textAnswer.value.trim() : selected.value.length > 0 })

function toggle(option: string) {
  if (result.value) return
  if (item.value?.question.question_type === 'multiple_choice') selected.value = selected.value.includes(option) ? selected.value.filter(x => x !== option) : [...selected.value, option]
  else selected.value = [option]
}
function answerValue(): AnswerValue { const t = item.value!.question.question_type; if (t === 'true_false') return boolAnswer.value!; if (t === 'short_answer') return textAnswer.value.trim(); return t === 'multiple_choice' ? selected.value : selected.value[0] }
function optionLabel(option: string, index: number) { return /^[A-Z][.、:：\s]/.test(option) ? option : `${String.fromCharCode(65 + index)}. ${option}` }
function isSelected(option: string) { return selected.value.includes(option) }

async function submit() {
  if (!item.value || !canSubmit.value) return
  submitting.value = true; error.value = ''
  const answer = answerValue()
  try {
    const response = await api.submitAnswer({ question_id: item.value.question.id, daily_task_item_id: item.value.id, answer, duration_seconds: Math.round((Date.now() - startedAt.value) / 1000), idempotency_key: `${state.task!.id}-${item.value.id}` })
    state.answers[item.value.id] = response
    if (!response.is_correct) await pollAnalysis(response.id, item.value.id)
  } catch (e) { error.value = e instanceof Error ? e.message : '提交失败，请重试' }
  finally { submitting.value = false }
}
const wait = (milliseconds: number) => new Promise(resolve => window.setTimeout(resolve, milliseconds))
async function pollAnalysis(answerId: number, itemId: number) {
  aiLoading.value = true
  try {
    for (let attempt = 0; attempt < 4; attempt++) {
      const response = await api.answerAnalysis(answerId)
      state.analyses[itemId] = response
      if (response.status !== 'pending') return
      if (attempt < 3) await wait(1500)
    }
  } catch { /* Standard explanation remains available as graceful fallback. */ }
  finally { aiLoading.value = false }
}
async function retryAnalysis() {
  if (!result.value || !item.value || aiLoading.value) return
  error.value = ''
  try {
    state.analyses[item.value.id] = await api.retryAnswerAnalysis(result.value.id)
    await pollAnalysis(result.value.id, item.value.id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'AI分析重试失败，请稍后再试'
  }
}
async function saveFeedback(feedback: DifficultyFeedback) {
  if (!result.value) return
  feedbackSaving.value = true; feedbackError.value = ''
  try {
    await api.updateAnswerFeedback(result.value.id, feedback)
    result.value.difficulty_feedback = feedback
  } catch (e) { feedbackError.value = e instanceof Error ? e.message : '反馈保存失败' }
  finally { feedbackSaving.value = false }
}
async function next() {
  if (nextUnansweredPosition.value) {
    await router.push(`/question/${nextUnansweredPosition.value}`)
    return
  }
  if (!state.task) return
  if (state.task.status === 'completed') {
    await router.push('/')
    return
  }
  completing.value = true; error.value = ''
  try {
    state.task = await api.completeTask(state.task.id)
    await router.push('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '暂时无法完成今日训练，请重试'
  } finally { completing.value = false }
}
function restoreSubmittedAnswer() {
  selected.value = []
  textAnswer.value = ''
  boolAnswer.value = null
  if (!result.value) return
  const answer = result.value.submitted_answer
  if (Array.isArray(answer)) selected.value = [...answer]
  else if (typeof answer === 'boolean') boolAnswer.value = answer
  else if (item.value?.question.question_type === 'short_answer') textAnswer.value = answer
  else selected.value = [answer]
}
async function resumePendingAnalysis() {
  if (result.value && analysisResponse.value?.status === 'pending' && !aiLoading.value) {
    await pollAnalysis(result.value.id, item.value!.id)
  }
}
onMounted(async () => {
  try {
    if (!state.task) state.task = await api.today()
    if (state.task && !Object.keys(state.answers).length) {
      const answers = await api.taskAnswers(state.task.id)
      restoreAnswers(answers)
    }
    restoreSubmittedAnswer()
    await resumePendingAnalysis()
  } catch { await router.replace('/') }
  finally { loading.value = false }
})
watch(position, () => {
  restoreSubmittedAnswer()
  error.value = ''
  feedbackError.value = ''
  startedAt.value = Date.now()
  void resumePendingAnalysis()
})
watch(result, restoreSubmittedAnswer)
</script>

<template>
  <main class="min-h-dvh px-5 pb-32 pt-[max(1.25rem,env(safe-area-inset-top))]">
    <LoadingState v-if="loading" />
    <template v-else-if="item">
      <header class="flex items-center justify-between"><button class="grid h-11 w-11 place-items-center rounded-full bg-white shadow-sm" aria-label="返回" @click="router.push('/')"><ArrowLeft :size="20"/></button><ProgressDots :current="position" :answered="answeredPositions"/><span class="w-11 text-right text-sm font-semibold">{{ position }}/6</span></header>
      <section class="mt-8"><div class="flex items-center gap-2 text-xs font-semibold text-leaf-600"><span class="rounded-full bg-leaf-50 px-3 py-1.5">{{ item.question.subject }}</span><span v-for="point in item.question.knowledge_points.slice(0, 1)" :key="point" class="rounded-full bg-slate-100 px-3 py-1.5 text-slate-500">{{ point }}</span></div><p class="mt-6 text-xs font-semibold uppercase tracking-[.18em] text-slate-400">{{ item.question.title }}</p><h1 class="mt-3 text-xl font-semibold leading-8"><RichText :text="item.question.content" block/></h1><p v-if="item.question.question_type === 'multiple_choice'" class="mt-3 text-xs text-slate-400">本题为多选题</p></section>
      <section v-if="item.question.question_type === 'true_false'" class="mt-8 grid grid-cols-2 gap-3"><button v-for="choice in [{v:true,l:'正确'},{v:false,l:'错误'}]" :key="choice.l" :disabled="!!result" class="rounded-2xl border bg-white p-5 font-semibold transition" :class="boolAnswer === choice.v ? 'border-leaf-500 bg-leaf-50 text-leaf-700' : 'border-slate-200'" @click="boolAnswer = choice.v">{{ choice.l }}</button></section>
      <section v-else-if="item.question.question_type === 'short_answer'" class="mt-8"><textarea v-model="textAnswer" :disabled="!!result" rows="5" class="w-full resize-none rounded-2xl border border-slate-200 bg-white p-4 text-base leading-7 shadow-sm focus:border-leaf-500 focus:outline-none" placeholder="在这里写下你的答案…" /></section>
      <section v-else class="mt-8 space-y-3"><button v-for="(option, index) in item.question.options" :key="option" :disabled="!!result" class="flex min-h-16 w-full items-center rounded-2xl border bg-white p-4 text-left text-sm leading-6 transition" :class="isSelected(option) ? 'border-leaf-500 bg-leaf-50 text-leaf-700 shadow-sm' : 'border-slate-200'" @click="toggle(option)"><span class="mr-3 grid h-7 w-7 shrink-0 place-items-center rounded-full border text-xs font-semibold" :class="isSelected(option) ? 'border-leaf-500 bg-leaf-600 text-white' : 'border-slate-200 text-slate-400'">{{ String.fromCharCode(65 + index) }}</span><RichText :text="optionLabel(option, index).replace(/^[A-Z][.、:：\s]+/, '')"/></button></section>
      <p v-if="error" class="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-600">{{ error }}</p>
      <section v-if="result" class="mt-8 overflow-hidden rounded-[1.75rem] bg-white shadow-soft"><div class="flex items-center gap-3 p-5" :class="result.is_correct ? 'bg-leaf-50 text-leaf-700' : 'bg-red-50 text-red-700'"><span class="grid h-10 w-10 place-items-center rounded-full text-white" :class="result.is_correct ? 'bg-leaf-600' : 'bg-coral'"><Check v-if="result.is_correct" :size="21"/><X v-else :size="21"/></span><div><h2 class="font-bold">{{ result.is_correct ? '答对了，很稳！' : '这道题再理一理' }}</h2><p class="mt-0.5 text-xs opacity-70">你的答案：{{ Array.isArray(result.submitted_answer) ? result.submitted_answer.join('、') : result.submitted_answer === true ? '正确' : result.submitted_answer === false ? '错误' : result.submitted_answer }}</p><p class="mt-0.5 text-xs opacity-70">正确答案：{{ Array.isArray(result.correct_answer) ? result.correct_answer.join('、') : result.correct_answer === true ? '正确' : result.correct_answer === false ? '错误' : result.correct_answer }}</p></div></div><div v-if="result.explanation" class="border-b border-slate-100 p-5"><div class="mb-2 flex items-center gap-2 text-sm font-semibold"><Lightbulb :size="17" class="text-amber-500"/>标准解析</div><RichText :text="result.explanation" block class="text-sm leading-7 text-slate-600"/></div><div v-if="!result.is_correct" class="border-b border-slate-100 p-5"><div class="mb-4 flex items-center gap-2 text-sm font-semibold"><Brain :size="18" class="text-leaf-600"/>AI 学习分析</div><div v-if="aiLoading" class="space-y-3"><div class="h-4 w-3/4 animate-pulse rounded bg-slate-100"/><div class="h-4 animate-pulse rounded bg-slate-100"/><div class="h-4 w-4/5 animate-pulse rounded bg-slate-100"/></div><div v-else-if="analysis" class="space-y-4 text-sm"><span class="inline-block rounded-lg bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700">{{ analysis.mistake_type }}</span><div><p class="text-xs font-semibold text-slate-400">为什么会错</p><p class="mt-1 leading-6">{{ analysis.reason }}</p></div><div><p class="text-xs font-semibold text-slate-400">薄弱知识点</p><span class="mt-2 inline-block rounded-lg bg-leaf-50 px-3 py-1.5 font-medium text-leaf-700">{{ analysis.knowledge_gap }}</span></div><div><p class="text-xs font-semibold text-slate-400">学习建议</p><p class="mt-1 leading-6">{{ analysis.suggestion }}</p></div><div><p class="text-xs font-semibold text-slate-400">接下来练什么</p><p class="mt-1 leading-6">{{ analysis.next_training }}</p></div></div><p v-else-if="analysisResponse?.status === 'pending'" class="text-sm leading-6 text-slate-400">分析仍在进行，你可以先看标准解析，稍后再回来查看。</p><div v-else class="text-sm leading-6 text-slate-400"><p>AI 分析暂时不可用，你仍可以先查看标准解析。</p><button v-if="analysisResponse?.status === 'failed'" class="mt-3 min-h-11 rounded-xl bg-leaf-50 px-4 font-semibold text-leaf-700" @click="retryAnalysis">重新生成AI分析</button></div></div><div class="p-5"><p class="text-sm font-semibold">这道题对你来说？</p><p class="mt-1 text-xs text-slate-400">可选反馈，帮助我们了解真实掌握情况</p><div class="mt-4 grid grid-cols-3 gap-2"><button v-for="choice in [{value:'easy',label:'很简单'},{value:'difficult',label:'有点困难'},{value:'dont_know',label:'完全不会'}]" :key="choice.value" :disabled="feedbackSaving" class="min-h-12 rounded-xl border px-2 text-sm font-medium transition" :class="result.difficulty_feedback === choice.value ? 'border-leaf-500 bg-leaf-50 text-leaf-700' : 'border-slate-200 text-slate-500'" @click="saveFeedback(choice.value as DifficultyFeedback)">{{ choice.label }}</button></div><p v-if="feedbackError" class="mt-3 text-xs text-red-600">{{ feedbackError }}</p></div></section>
      <div class="safe-bottom fixed inset-x-0 bottom-0 z-20 mx-auto max-w-lg border-t border-black/5 bg-paper/95 p-4 backdrop-blur-xl"><button v-if="!result" :disabled="!canSubmit || submitting" class="h-14 w-full rounded-2xl bg-ink font-semibold text-white transition active:scale-[.99] disabled:bg-slate-200 disabled:text-slate-400" @click="submit">{{ submitting ? '正在提交…' : '提交答案' }}</button><button v-else :disabled="completing" class="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-leaf-600 font-semibold text-white disabled:opacity-60" @click="next">{{ completing ? '正在完成…' : nextUnansweredPosition ? '下一道未完成题' : state.task?.status === 'completed' ? '返回今日任务' : '完成今日训练' }}<ArrowRight :size="19"/></button></div>
    </template>
  </main>
</template>
