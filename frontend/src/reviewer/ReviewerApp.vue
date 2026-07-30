<script setup lang="ts">
import katex from "katex";
import "katex/dist/katex.min.css";
import { computed, nextTick, onMounted, ref, watch } from "vue";

type ReviewDecision = "PASS" | "REVISE" | "REJECT" | "";

interface Question {
  subject: string;
  chapter: string;
  knowledge_points: string[];
  difficulty: number;
  type: string;
  question: string;
  options: string[];
  answer: string | string[];
  solution: string;
  source?: string;
  title?: string;
  tags?: string[];
  _key: string;
  _file: string;
}

interface ReviewRecord {
  decision: ReviewDecision;
  note: string;
  updated_at: string;
}

interface ServerBatch {
  name: string;
  updated_at: string;
}

const questions = ref<Question[]>([]);
const records = ref<Record<string, ReviewRecord>>({});
const currentIndex = ref(0);
const subjectFilter = ref("全部");
const decisionFilter = ref("全部");
const answerVisible = ref(false);
const autoAdvancePass = ref(
  localStorage.getItem("shiguang-question-review:auto-advance-pass") !== "false",
);
const loadingError = ref("");
const batchId = ref("");
const batchName = ref("");
const serverBatches = ref<ServerBatch[]>([]);
const selectedServerBatch = ref("");
const serverSaveState = ref<"idle" | "saving" | "saved" | "error">("idle");
const fileInput = ref<HTMLInputElement | null>(null);
let saveTimer: ReturnType<typeof setTimeout> | undefined;

const subjects = computed(() => [
  "全部",
  ...Array.from(new Set(questions.value.map((item) => item.subject))),
]);

const filteredQuestions = computed(() =>
  questions.value.filter((item) => {
    const record = records.value[item._key];
    const subjectMatched =
      subjectFilter.value === "全部" || item.subject === subjectFilter.value;
    const decisionMatched =
      decisionFilter.value === "全部" ||
      (decisionFilter.value === "未审核" && !record?.decision) ||
      (decisionFilter.value === "需处理" &&
        ["REVISE", "REJECT"].includes(record?.decision ?? "")) ||
      record?.decision === decisionFilter.value;
    return subjectMatched && decisionMatched;
  }),
);

const currentQuestion = computed(() => filteredQuestions.value[currentIndex.value]);
const currentRecord = computed(
  () =>
    records.value[currentQuestion.value?._key] ?? {
      decision: "",
      note: "",
      updated_at: "",
    },
);

const summary = computed(() => {
  const values = questions.value.map((item) => records.value[item._key]?.decision ?? "");
  return {
    total: questions.value.length,
    reviewed: values.filter(Boolean).length,
    pass: values.filter((value) => value === "PASS").length,
    revise: values.filter((value) => value === "REVISE").length,
    reject: values.filter((value) => value === "REJECT").length,
  };
});

const progress = computed(() =>
  summary.value.total
    ? Math.round((summary.value.reviewed / summary.value.total) * 100)
    : 0,
);

function storageKey() {
  return `shiguang-question-review:${batchId.value}`;
}

function stableQuestionKey(question: Omit<Question, "_key" | "_file">) {
  return [
    question.source ?? "",
    question.title ?? "",
    question.subject,
    question.question,
  ].join("|");
}

function validateQuestion(raw: unknown, file: string, index: number): Question {
  if (!raw || typeof raw !== "object") {
    throw new Error(`${file} 第${index + 1}题不是对象`);
  }
  const item = raw as Record<string, unknown>;
  const requiredStrings = ["subject", "chapter", "type", "question", "solution"] as const;
  for (const field of requiredStrings) {
    if (typeof item[field] !== "string" || !item[field]) {
      throw new Error(`${file} 第${index + 1}题缺少 ${field}`);
    }
  }
  if (!Array.isArray(item.options) || item.options.length < 2) {
    throw new Error(`${file} 第${index + 1}题 options 无效`);
  }
  if (!Array.isArray(item.knowledge_points) || !item.knowledge_points.length) {
    throw new Error(`${file} 第${index + 1}题 knowledge_points 无效`);
  }
  if (
    typeof item.answer !== "string" &&
    !Array.isArray(item.answer)
  ) {
    throw new Error(`${file} 第${index + 1}题 answer 无效`);
  }
  return {
    subject: item.subject as string,
    chapter: item.chapter as string,
    knowledge_points: item.knowledge_points.map(String),
    difficulty: Number(item.difficulty),
    type: item.type as string,
    question: item.question as string,
    options: item.options.map(String),
    answer: item.answer as string | string[],
    solution: item.solution as string,
    source: typeof item.source === "string" ? item.source : undefined,
    title: typeof item.title === "string" ? item.title : undefined,
    tags: Array.isArray(item.tags) ? item.tags.map(String) : undefined,
    _key: stableQuestionKey(item as unknown as Omit<Question, "_key" | "_file">),
    _file: file,
  };
}

async function digest(text: string) {
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function loadFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  if (!input.files?.length) return;
  loadingError.value = "";
  try {
    const files = Array.from(input.files).sort((a, b) => a.name.localeCompare(b.name));
    const loaded: Question[] = [];
    const identityParts: string[] = [];
    for (const file of files) {
      const text = await file.text();
      const payload = JSON.parse(text) as { questions?: unknown[] } | unknown[];
      const rawQuestions = Array.isArray(payload) ? payload : payload.questions;
      if (!Array.isArray(rawQuestions)) {
        throw new Error(`${file.name} 顶层必须是数组或包含 questions 数组`);
      }
      identityParts.push(`${file.name}:${await digest(text)}`);
      rawQuestions.forEach((item, index) => {
        loaded.push(validateQuestion(item, file.name, index));
      });
    }
    const uniqueKeys = new Set(loaded.map((item) => item._key));
    if (uniqueKeys.size !== loaded.length) {
      throw new Error("所选文件中存在重复题目，请先去重");
    }
    batchId.value = (await digest(identityParts.join("|"))).slice(0, 20);
    batchName.value = files.map((file) => file.name).join(" + ");
    selectedServerBatch.value = "";
    questions.value = loaded;
    restoreRecords();
    currentIndex.value = 0;
    answerVisible.value = false;
  } catch (error) {
    loadingError.value = error instanceof Error ? error.message : "文件读取失败";
  } finally {
    input.value = "";
  }
}

function restoreRecords() {
  const saved = localStorage.getItem(storageKey());
  if (!saved) {
    records.value = {};
    return;
  }
  try {
    records.value = JSON.parse(saved) as Record<string, ReviewRecord>;
  } catch {
    records.value = {};
  }
}

function saveRecords() {
  if (!batchId.value) return;
  localStorage.setItem(storageKey(), JSON.stringify(records.value));
}

function reviewPayload() {
  return {
    schema_version: "shiguang-question-review-v1",
    batch_id: batchId.value,
    batch_name: batchName.value,
    exported_at: new Date().toISOString(),
    summary: summary.value,
    reviews: questions.value.map((question, index) => ({
      index: index + 1,
      file: question._file,
      source: question.source ?? "",
      title: question.title ?? "",
      subject: question.subject,
      question: question.question,
      decision: records.value[question._key]?.decision ?? "",
      note: records.value[question._key]?.note ?? "",
      updated_at: records.value[question._key]?.updated_at ?? "",
    })),
  };
}

async function saveServerResult() {
  if (!selectedServerBatch.value) return;
  serverSaveState.value = "saving";
  try {
    const response = await fetch(
      `/review-api/result?name=${encodeURIComponent(selectedServerBatch.value)}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reviewPayload()),
      },
    );
    if (!response.ok) throw new Error("保存失败");
    serverSaveState.value = "saved";
  } catch {
    serverSaveState.value = "error";
  }
}

function scheduleServerSave(immediate = false) {
  if (!selectedServerBatch.value) return;
  if (saveTimer) clearTimeout(saveTimer);
  if (immediate) {
    void saveServerResult();
    return;
  }
  serverSaveState.value = "saving";
  saveTimer = setTimeout(() => void saveServerResult(), 500);
}

async function setDecision(decision: Exclude<ReviewDecision, "">) {
  const question = currentQuestion.value;
  if (!question) return;
  records.value = {
    ...records.value,
    [question._key]: {
      decision,
      note: currentRecord.value.note,
      updated_at: new Date().toISOString(),
    },
  };
  saveRecords();
  scheduleServerSave(true);
  if (decision === "PASS" && autoAdvancePass.value) {
    await nextTick();
    if (decisionFilter.value !== "未审核") move(1);
  }
}

function updateNote(event: Event) {
  const question = currentQuestion.value;
  if (!question) return;
  records.value = {
    ...records.value,
    [question._key]: {
      decision: currentRecord.value.decision,
      note: (event.target as HTMLTextAreaElement).value,
      updated_at: new Date().toISOString(),
    },
  };
  saveRecords();
  scheduleServerSave();
}

function move(offset: number) {
  if (!filteredQuestions.value.length) return;
  currentIndex.value = Math.min(
    Math.max(currentIndex.value + offset, 0),
    filteredQuestions.value.length - 1,
  );
  answerVisible.value = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function jumpTo(position: number) {
  if (!Number.isFinite(position) || !filteredQuestions.value.length) return;
  currentIndex.value = Math.min(
    Math.max(Math.trunc(position) - 1, 0),
    filteredQuestions.value.length - 1,
  );
  answerVisible.value = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function toggleAutoAdvance() {
  localStorage.setItem(
    "shiguang-question-review:auto-advance-pass",
    String(autoAdvancePass.value),
  );
}

function questionDecision(question: Question) {
  return records.value[question._key]?.decision ?? "";
}

function exportReviews() {
  const payload = reviewPayload();
  const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], {
    type: "application/json;charset=utf-8",
  });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `question_review_${batchId.value}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function loadServerBatch(name: string) {
  if (!name) return;
  loadingError.value = "";
  try {
    const response = await fetch(`/review-api/batch?name=${encodeURIComponent(name)}`);
    if (!response.ok) throw new Error("项目审查批次加载失败");
    const data = (await response.json()) as {
      name: string;
      payload: { questions?: unknown[] } | unknown[];
      result?: {
        reviews?: Array<{
          source?: string;
          decision?: ReviewDecision;
          note?: string;
          updated_at?: string;
        }>;
      } | null;
    };
    const rawQuestions = Array.isArray(data.payload)
      ? data.payload
      : data.payload.questions;
    if (!Array.isArray(rawQuestions)) throw new Error("批次中缺少 questions 数组");
    const loaded = rawQuestions.map((item, index) =>
      validateQuestion(item, data.name, index),
    );
    batchId.value = (await digest(`${data.name}:${JSON.stringify(data.payload)}`)).slice(
      0,
      20,
    );
    batchName.value = data.name;
    selectedServerBatch.value = data.name;
    questions.value = loaded;
    const savedReviews = new Map(
      (data.result?.reviews ?? []).map((review) => [review.source ?? "", review]),
    );
    records.value = Object.fromEntries(
      loaded.flatMap((question) => {
        const saved = savedReviews.get(question.source ?? "");
        return saved
          ? [
              [
                question._key,
                {
                  decision: saved.decision ?? "",
                  note: saved.note ?? "",
                  updated_at: saved.updated_at ?? "",
                },
              ],
            ]
          : [];
      }),
    );
    saveRecords();
    currentIndex.value = 0;
    answerVisible.value = false;
    serverSaveState.value = "idle";
  } catch (error) {
    loadingError.value = error instanceof Error ? error.message : "项目批次加载失败";
  }
}

async function discoverServerBatches() {
  try {
    const response = await fetch("/review-api/batches");
    if (!response.ok) return;
    const data = (await response.json()) as { batches: ServerBatch[] };
    serverBatches.value = data.batches;
    if (data.batches.length) {
      await loadServerBatch(data.batches[0].name);
    }
  } catch {
    // Production builds can still use manual local-file loading.
  }
}

function clearBatchProgress() {
  if (!batchId.value || !window.confirm("确定清空当前批次的全部审核记录吗？")) return;
  localStorage.removeItem(storageKey());
  records.value = {};
}

function renderMath(text: string) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped.replace(/\$([^$]+)\$/g, (_, expression: string) => {
    try {
      return katex.renderToString(expression, {
        throwOnError: false,
        displayMode: false,
      });
    } catch {
      return `$${expression}$`;
    }
  });
}

watch([subjectFilter, decisionFilter], () => {
  currentIndex.value = 0;
  answerVisible.value = false;
});

watch(filteredQuestions, (items) => {
  if (currentIndex.value >= items.length) {
    currentIndex.value = Math.max(items.length - 1, 0);
  }
});

watch(currentQuestion, async () => {
  await nextTick();
  document.title = currentQuestion.value
    ? `${currentQuestion.value.subject}审核｜拾光题库`
    : "拾光题库审查工具";
});

onMounted(() => {
  void discoverServerBatches();
  window.addEventListener("keydown", (event) => {
    if ((event.target as HTMLElement)?.tagName === "TEXTAREA") return;
    if (event.key === "ArrowLeft") move(-1);
    if (event.key === "ArrowRight") move(1);
  });
});
</script>

<template>
  <main class="review-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">拾光 · 教研工具</p>
        <h1>题库审查</h1>
      </div>
      <div v-if="questions.length" class="header-actions">
        <button class="secondary" @click="fileInput?.click()">更换批次</button>
        <button class="primary" @click="exportReviews">导出结果</button>
      </div>
      <input
        ref="fileInput"
        class="hidden-input"
        type="file"
        accept=".json,application/json"
        multiple
        @change="loadFiles"
      />
    </header>

    <section v-if="serverBatches.length" class="batch-loader">
      <label>
        项目待审批次
        <select
          v-model="selectedServerBatch"
          @change="loadServerBatch(selectedServerBatch)"
        >
          <option v-for="batch in serverBatches" :key="batch.name" :value="batch.name">
            {{ batch.name }}
          </option>
        </select>
      </label>
      <span v-if="selectedServerBatch" :class="['save-state', serverSaveState]">
        {{
          serverSaveState === "saving"
            ? "正在写入项目…"
            : serverSaveState === "error"
              ? "自动保存失败"
              : serverSaveState === "saved"
                ? "已自动保存到项目"
                : "选择结论后自动保存"
        }}
      </span>
      <button class="secondary" @click="fileInput?.click()">手动载入其他文件</button>
    </section>

    <section v-if="!questions.length" class="empty-card">
      <div class="empty-icon">审</div>
      <h2>载入题库 JSON 开始审查</h2>
      <p>支持一次选择一个或多个现有题库文件。文件不会上传，审核数据只保存在本机浏览器。</p>
      <button class="primary large" @click="fileInput?.click()">选择 JSON 文件</button>
      <p v-if="loadingError" class="error">{{ loadingError }}</p>
      <div class="format-note">
        支持顶层 <code>{"{ questions: [...] }"}</code> 或题目数组格式。
      </div>
    </section>

    <template v-else>
      <section class="dashboard">
        <div class="batch-title">
          <span>当前批次</span>
          <strong>{{ batchName }}</strong>
        </div>
        <div class="stats">
          <span>总计 <strong>{{ summary.total }}</strong></span>
          <span>已审 <strong>{{ summary.reviewed }}</strong></span>
          <span class="pass-text">通过 {{ summary.pass }}</span>
          <span class="revise-text">修改 {{ summary.revise }}</span>
          <span class="reject-text">拒绝 {{ summary.reject }}</span>
        </div>
        <div class="progress-track">
          <div class="progress-value" :style="{ width: `${progress}%` }"></div>
        </div>
      </section>

      <section class="filters">
        <label>
          学科
          <select v-model="subjectFilter">
            <option v-for="subject in subjects" :key="subject">{{ subject }}</option>
          </select>
        </label>
        <label>
          状态
          <select v-model="decisionFilter">
            <option>全部</option>
            <option>未审核</option>
            <option>需处理</option>
            <option>PASS</option>
            <option>REVISE</option>
            <option>REJECT</option>
          </select>
        </label>
        <span class="filtered-count">筛选后 {{ filteredQuestions.length }} 题</span>
        <label class="jump-control">
          跳到题号
          <input
            :value="currentIndex + 1"
            type="number"
            min="1"
            :max="filteredQuestions.length"
            @change="jumpTo(Number(($event.target as HTMLInputElement).value))"
          />
        </label>
      </section>

      <section v-if="currentQuestion" class="question-layout">
        <article class="question-card">
          <div class="question-meta">
            <span class="subject-chip">{{ currentQuestion.subject }}</span>
            <span>{{ currentQuestion.chapter }}</span>
            <span>难度 {{ currentQuestion.difficulty }}</span>
            <span>{{ currentQuestion.type }}</span>
            <span class="position">
              {{ currentIndex + 1 }} / {{ filteredQuestions.length }}
            </span>
          </div>

          <h2 v-if="currentQuestion.title">{{ currentQuestion.title }}</h2>
          <div class="stem math-content" v-html="renderMath(currentQuestion.question)"></div>

          <ol class="options">
            <li v-for="(option, index) in currentQuestion.options" :key="index">
              <span class="option-label">{{ String.fromCharCode(65 + index) }}</span>
              <span class="math-content" v-html="renderMath(option)"></span>
            </li>
          </ol>

          <div class="knowledge-row">
            <span v-for="point in currentQuestion.knowledge_points" :key="point">
              {{ point }}
            </span>
          </div>

          <button class="answer-toggle" @click="answerVisible = !answerVisible">
            {{ answerVisible ? "隐藏答案与解析" : "完成独立作答后，查看答案与解析" }}
          </button>

          <div v-if="answerVisible" class="answer-panel">
            <p>
              <strong>原答案：</strong>
              {{ Array.isArray(currentQuestion.answer) ? currentQuestion.answer.join("、") : currentQuestion.answer }}
            </p>
            <div>
              <strong>原解析：</strong>
              <p class="math-content solution" v-html="renderMath(currentQuestion.solution)"></p>
            </div>
            <p class="source"><strong>来源：</strong>{{ currentQuestion.source || "未填写" }}</p>
          </div>
        </article>

        <aside class="review-panel">
          <h3>审核结论</h3>
          <label class="auto-advance">
            <input v-model="autoAdvancePass" type="checkbox" @change="toggleAutoAdvance" />
            PASS 后自动下一题
          </label>
          <div class="decision-grid">
            <button
              :class="{ selected: currentRecord.decision === 'PASS' }"
              class="pass"
              @click="setDecision('PASS')"
            >
              PASS
              <small>可以进入候选库</small>
            </button>
            <button
              :class="{ selected: currentRecord.decision === 'REVISE' }"
              class="revise"
              @click="setDecision('REVISE')"
            >
              REVISE
              <small>修改后重新审核</small>
            </button>
            <button
              :class="{ selected: currentRecord.decision === 'REJECT' }"
              class="reject"
              @click="setDecision('REJECT')"
            >
              REJECT
              <small>不进入题库</small>
            </button>
          </div>
          <label class="note-label">
            问题与修改建议
            <textarea
              :value="currentRecord.note"
              placeholder="例如：B、C均可成立；公式OCR错误；解析缺少关键步骤……"
              @input="updateNote"
            ></textarea>
          </label>
          <p class="autosave">
            {{
              selectedServerBatch
                ? "审核结果实时写入项目，无需导出"
                : "审核进度自动保存在当前浏览器"
            }}
          </p>
          <div class="question-navigator">
            <div class="navigator-title">
              <strong>题号跳转</strong>
              <span>{{ filteredQuestions.length }}题</span>
            </div>
            <div class="number-grid">
              <button
                v-for="(question, index) in filteredQuestions"
                :key="question._key"
                :class="[
                  questionDecision(question).toLowerCase(),
                  { current: index === currentIndex },
                ]"
                :title="`${question.subject}｜${questionDecision(question) || '未审核'}`"
                @click="jumpTo(index + 1)"
              >
                {{ index + 1 }}
              </button>
            </div>
          </div>
        </aside>
      </section>

      <section v-else class="no-result">
        当前筛选条件下没有题目。
      </section>

      <nav class="bottom-nav">
        <button class="secondary" :disabled="currentIndex === 0" @click="move(-1)">
          ← 上一题
        </button>
        <button
          class="secondary"
          :disabled="currentIndex >= filteredQuestions.length - 1"
          @click="move(1)"
        >
          下一题 →
        </button>
      </nav>

      <footer>
        <button class="danger-link" @click="clearBatchProgress">清空本批审核进度</button>
      </footer>
    </template>
  </main>
</template>
