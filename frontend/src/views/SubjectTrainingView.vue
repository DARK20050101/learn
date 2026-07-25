<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, BookOpen } from 'lucide-vue-next'
import LoadingState from '../components/LoadingState.vue'
import { api } from '../services/api'
import type { SubjectTrainingCatalog } from '../types'

const router = useRouter()
const catalog = ref<SubjectTrainingCatalog | null>(null)
const subject = ref('')
const chapter = ref('')
const knowledgePointCode = ref('')
const difficulty = ref<number | null>(null)
const questionCount = ref(10)
const loading = ref(true)
const creating = ref(false)
const error = ref('')
const selectedSubject = computed(() => catalog.value?.subjects.find(item => item.name === subject.value))
const chapters = computed(() => selectedSubject.value?.chapters ?? [])
const selectedChapter = computed(() => chapters.value.find(item => item.name === chapter.value))
const points = computed(() => selectedChapter.value?.knowledge_points ?? [])
const selectedPoint = computed(() => points.value.find(item => item.code === knowledgePointCode.value))
const selectedScope = computed(() => selectedPoint.value ?? selectedChapter.value ?? selectedSubject.value)
const available = computed(() => difficulty.value
  ? selectedScope.value?.difficulty_counts[difficulty.value] ?? 0
  : selectedScope.value?.question_count ?? 0)
const countOptions = computed(() => [...new Set([5, 10, 15, 20, Math.min(20, available.value)])].filter(count => count > 0 && count <= available.value).sort((a, b) => a - b))
const canCreate = computed(() => !!subject.value && available.value > 0 && questionCount.value <= available.value)

watch(subject, () => { chapter.value = ''; knowledgePointCode.value = ''; difficulty.value = null })
watch(chapter, () => { knowledgePointCode.value = ''; difficulty.value = null })
watch(knowledgePointCode, () => { difficulty.value = null })
watch(available, value => {
  if (value > 0 && questionCount.value > value) questionCount.value = Math.min(10, value)
})

async function start() {
  if (!canCreate.value) return
  creating.value = true; error.value = ''
  try {
    const session = await api.createSubjectTraining({
      subject: subject.value,
      ...(chapter.value ? { chapter: chapter.value } : {}),
      ...(knowledgePointCode.value ? { knowledge_point_code: knowledgePointCode.value } : {}),
      ...(difficulty.value ? { difficulty: difficulty.value } : {}),
      question_count: questionCount.value,
    })
    await router.push(`/training/${session.id}/1`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '专项训练创建失败，请重试'
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  try {
    catalog.value = await api.subjectTrainingCatalog()
    subject.value = catalog.value.subjects[0]?.name ?? ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '题库范围加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="min-h-dvh px-5 pb-10 pt-[max(1.25rem,env(safe-area-inset-top))]">
    <header class="flex items-center gap-4"><button class="grid h-11 w-11 place-items-center rounded-full bg-white shadow-sm" aria-label="返回" @click="router.push('/')"><ArrowLeft :size="20"/></button><div><h1 class="text-xl font-bold">学科专项训练</h1><p class="mt-1 text-xs text-slate-400">选择一个范围，集中练习</p></div></header>
    <LoadingState v-if="loading" class="mt-20"/>
    <section v-else-if="catalog?.subjects.length" class="mt-8 space-y-6">
      <div class="rounded-[1.75rem] bg-ink p-6 text-white"><BookOpen :size="25" class="text-[#e9c985]"/><h2 class="mt-5 text-xl font-bold">今天想加练什么？</h2><p class="mt-2 text-sm text-white/60">推荐先选一个薄弱知识点，每次 5—10 题。</p></div>
      <label class="block"><span class="mb-2 block text-sm font-semibold">学科</span><select v-model="subject" class="h-14 w-full rounded-2xl border border-slate-200 bg-white px-4 text-base outline-none focus:border-leaf-500"><option v-for="item in catalog.subjects" :key="item.name" :value="item.name">{{ item.name }}（{{ item.question_count }}题）</option></select></label>
      <label class="block"><span class="mb-2 block text-sm font-semibold">章节（可选）</span><select v-model="chapter" class="h-14 w-full rounded-2xl border border-slate-200 bg-white px-4 text-base outline-none focus:border-leaf-500"><option value="">全部章节</option><option v-for="item in chapters" :key="item.name" :value="item.name">{{ item.name }}（{{ item.question_count }}题）</option></select></label>
      <label v-if="chapter" class="block"><span class="mb-2 block text-sm font-semibold">知识点（可选）</span><select v-model="knowledgePointCode" class="h-14 w-full rounded-2xl border border-slate-200 bg-white px-4 text-base outline-none focus:border-leaf-500"><option value="">本章综合</option><option v-for="item in points" :key="item.code" :value="item.code">{{ item.name }}（{{ item.question_count }}题）</option></select></label>
      <div><span class="mb-3 block text-sm font-semibold">难度（可选）</span><div class="grid grid-cols-3 gap-2"><button v-for="level in [null, 1, 2, 3, 4, 5]" :key="level ?? 'all'" class="min-h-12 rounded-xl border px-3 text-sm font-semibold" :class="difficulty === level ? 'border-leaf-500 bg-leaf-50 text-leaf-700' : 'border-slate-200 bg-white'" @click="difficulty = level">{{ level ? `难度 ${level}` : '不限' }}</button></div></div>
      <div><span class="mb-3 block text-sm font-semibold">题量</span><div class="flex flex-wrap gap-2"><button v-for="count in countOptions" :key="count" class="min-h-12 min-w-16 flex-1 rounded-xl border px-3 font-semibold" :class="questionCount === count ? 'border-leaf-500 bg-leaf-50 text-leaf-700' : 'border-slate-200 bg-white'" @click="questionCount = count">{{ count }}题</button></div><p class="mt-2 text-xs text-slate-400">当前范围可用 {{ available }} 题</p></div>
      <p v-if="error" class="rounded-xl bg-red-50 p-3 text-sm text-red-600">{{ error }}</p>
      <button :disabled="!canCreate || creating" class="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-leaf-600 font-semibold text-white disabled:bg-slate-200 disabled:text-slate-400" @click="start">{{ creating ? '正在生成…' : '开始专项训练' }}<ArrowRight v-if="!creating" :size="19"/></button>
    </section>
    <section v-else class="mt-16 rounded-2xl bg-white p-6 text-center"><h2 class="font-bold">暂无可用题目</h2><p class="mt-2 text-sm text-slate-400">请先导入带学科和章节信息的题目。</p><p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p></section>
  </main>
</template>
