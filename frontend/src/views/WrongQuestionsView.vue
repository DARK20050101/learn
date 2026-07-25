<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { AlertCircle, Brain, ChevronDown, ChevronUp, Dumbbell, Lightbulb, RefreshCw } from 'lucide-vue-next'
import AppNav from '../components/AppNav.vue'
import LoadingState from '../components/LoadingState.vue'
import { api } from '../services/api'
import type { AnswerValue, WrongQuestion, WrongQuestionSort } from '../types'

const loading = ref(true)
const router = useRouter()
const error = ref('')
const items = ref<WrongQuestion[]>([])
const catalogItems = ref<WrongQuestion[]>([])
const subject = ref('')
const knowledgePointCode = ref('')
const sort = ref<WrongQuestionSort>('error_count_desc')
const expandedId = ref<number | null>(null)
const practicingId = ref<number | null>(null)
const subjects = ['', '数学', '物理', '英语']
const knowledgePoints = computed(() => {
  const source = subject.value
    ? catalogItems.value.filter(item => item.subject === subject.value)
    : catalogItems.value
  const unique = new Map(source.map(item => [
    item.knowledge_point_code,
    { code: item.knowledge_point_code, name: item.knowledge_point_name },
  ]))
  return [...unique.values()].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
})

function displayAnswer(value: AnswerValue) {
  if (Array.isArray(value)) return value.join('、')
  if (value === true) return '正确'
  if (value === false) return '错误'
  return value
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await api.wrongQuestions({
      ...(subject.value ? { subject: subject.value } : {}),
      ...(knowledgePointCode.value ? { knowledge_point_code: knowledgePointCode.value } : {}),
      sort: sort.value,
    })
    items.value = result.items
    if (!subject.value && !knowledgePointCode.value && !catalogItems.value.length) {
      catalogItems.value = result.items
    }
    if (expandedId.value && !items.value.some(item => item.question_id === expandedId.value)) {
      expandedId.value = null
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '错题本加载失败，请重试'
  } finally {
    loading.value = false
  }
}

async function practice(item: WrongQuestion) {
  practicingId.value = item.question_id
  error.value = ''
  try {
    const session = await api.practiceWrongQuestion(item.question_id)
    await router.push(`/training/${session.id}/1`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '暂时无法开始错题重练'
  } finally {
    practicingId.value = null
  }
}

watch(subject, () => {
  knowledgePointCode.value = ''
  void load()
})
watch(knowledgePointCode, () => { void load() })
watch(sort, () => { void load() })
onMounted(load)
</script>

<template>
  <main class="min-h-dvh px-5 pb-28 pt-[max(1.5rem,env(safe-area-inset-top))]">
    <header>
      <p class="text-sm font-medium text-leaf-700">学习回顾</p>
      <h1 class="mt-1 text-2xl font-bold">错题本</h1>
      <p class="mt-2 text-sm leading-6 text-slate-500">看清错误原因，比重复做更多题更重要。</p>
    </header>

    <section class="mt-6 space-y-3">
      <div class="flex gap-2 overflow-x-auto pb-1">
        <button
          v-for="value in subjects"
          :key="value || 'all'"
          class="min-h-11 shrink-0 rounded-xl border px-4 text-sm font-semibold"
          :class="subject === value ? 'border-leaf-500 bg-leaf-50 text-leaf-700' : 'border-slate-200 bg-white text-slate-500'"
          @click="subject = value"
        >{{ value || '全部' }}</button>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <label class="relative">
          <select v-model="knowledgePointCode" class="h-12 w-full appearance-none rounded-xl border border-slate-200 bg-white pl-3 pr-9 text-sm outline-none focus:border-leaf-500">
            <option value="">全部知识点</option>
            <option v-for="point in knowledgePoints" :key="point.code" :value="point.code">{{ point.name }}</option>
          </select>
          <ChevronDown :size="16" class="pointer-events-none absolute right-3 top-4 text-slate-400"/>
        </label>
        <label class="relative">
          <select v-model="sort" class="h-12 w-full appearance-none rounded-xl border border-slate-200 bg-white pl-3 pr-9 text-sm outline-none focus:border-leaf-500">
            <option value="error_count_desc">错误次数优先</option>
            <option value="recent_desc">最近错误优先</option>
          </select>
          <ChevronDown :size="16" class="pointer-events-none absolute right-3 top-4 text-slate-400"/>
        </label>
      </div>
    </section>

    <LoadingState v-if="loading" class="mt-16"/>
    <section v-else-if="error" class="mt-10 rounded-2xl bg-red-50 p-6 text-center text-red-600">
      <AlertCircle :size="30" class="mx-auto"/>
      <p class="mt-3 text-sm">{{ error }}</p>
      <button class="mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold" @click="load"><RefreshCw :size="16"/>重新加载</button>
    </section>
    <section v-else-if="!items.length" class="mt-10 rounded-[1.75rem] bg-white p-8 text-center shadow-sm">
      <span class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-leaf-50 text-leaf-700"><Lightbulb :size="26"/></span>
      <h2 class="mt-5 font-bold">{{ subject || knowledgePointCode ? '当前筛选下没有错题' : '错题本还是空的' }}</h2>
      <p class="mt-2 text-sm leading-6 text-slate-400">{{ subject || knowledgePointCode ? '换个学科或知识点看看。' : '完成训练后，答错的题会自动整理到这里。' }}</p>
    </section>
    <section v-else class="mt-6 space-y-3">
      <p class="text-xs text-slate-400">共 {{ items.length }} 道历史错题</p>
      <article v-for="item in items" :key="item.question_id" class="overflow-hidden rounded-2xl border border-black/[.04] bg-white shadow-sm">
        <button class="flex min-h-24 w-full items-center gap-4 p-4 text-left" @click="expandedId = expandedId === item.question_id ? null : item.question_id">
          <span class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-red-50 text-sm font-bold text-coral">×{{ item.error_count }}</span>
          <span class="min-w-0 flex-1">
            <span class="flex flex-wrap items-center gap-2 text-xs">
              <span class="font-semibold text-leaf-700">{{ item.subject }}</span>
              <span class="text-slate-300">·</span>
              <span class="truncate text-slate-500">{{ item.knowledge_point_name }}</span>
            </span>
            <span class="mt-2 block truncate text-sm font-semibold">{{ item.title }}</span>
            <span class="mt-1 block text-xs text-slate-400">最近答错 {{ formatDate(item.last_wrong_at) }} · 难度{{ item.difficulty }}</span>
          </span>
          <ChevronUp v-if="expandedId === item.question_id" :size="18" class="shrink-0 text-slate-400"/>
          <ChevronDown v-else :size="18" class="shrink-0 text-slate-400"/>
        </button>

        <div v-if="expandedId === item.question_id" class="border-t border-slate-100 px-5 pb-5">
          <div class="py-5">
            <p class="whitespace-pre-line text-base font-semibold leading-7">{{ item.content }}</p>
            <ol v-if="item.options?.length" class="mt-4 space-y-2 text-sm text-slate-600">
              <li v-for="(option, index) in item.options" :key="option" class="rounded-xl bg-slate-50 px-3 py-2.5">{{ String.fromCharCode(65 + index) }}. {{ option }}</li>
            </ol>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="rounded-xl bg-red-50 p-3"><p class="text-xs font-semibold text-red-400">我的答案</p><p class="mt-1 break-words font-medium text-red-700">{{ displayAnswer(item.submitted_answer) }}</p></div>
            <div class="rounded-xl bg-leaf-50 p-3"><p class="text-xs font-semibold text-leaf-500">正确答案</p><p class="mt-1 break-words font-medium text-leaf-800">{{ displayAnswer(item.correct_answer) }}</p></div>
          </div>
          <div v-if="item.explanation" class="mt-4 rounded-xl bg-amber-50/70 p-4">
            <div class="flex items-center gap-2 text-sm font-semibold"><Lightbulb :size="17" class="text-amber-500"/>标准解析</div>
            <p class="mt-2 whitespace-pre-line text-sm leading-6 text-slate-600">{{ item.explanation }}</p>
          </div>
          <div class="mt-4 rounded-xl bg-slate-50 p-4">
            <div class="flex items-center gap-2 text-sm font-semibold"><Brain :size="17" class="text-leaf-600"/>AI错因分析</div>
            <div v-if="item.ai_analysis" class="mt-3 space-y-3 text-sm leading-6">
              <span class="inline-block rounded-lg bg-white px-3 py-1 text-xs font-semibold text-amber-700">{{ item.ai_analysis.mistake_type }}</span>
              <p>{{ item.ai_analysis.reason }}</p>
              <p class="text-leaf-700">建议：{{ item.ai_analysis.suggestion }}</p>
              <p class="text-slate-500">接下来：{{ item.ai_analysis.next_training }}</p>
            </div>
            <p v-else-if="item.analysis_status === 'pending'" class="mt-2 text-sm text-slate-400">分析仍在进行，可以先看标准解析。</p>
            <p v-else class="mt-2 text-sm text-slate-400">AI分析暂不可用，可以先按标准解析复盘。</p>
          </div>
          <button :disabled="practicingId === item.question_id" class="mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-ink px-4 text-sm font-semibold text-white disabled:opacity-60" @click="practice(item)">
            <Dumbbell :size="17"/>{{ practicingId === item.question_id ? '正在准备…' : '再练一次' }}
          </button>
        </div>
      </article>
    </section>
    <AppNav/>
  </main>
</template>
