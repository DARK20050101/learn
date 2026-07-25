# Phase 10 题库生产流程设计

## 1. 目标与边界

Phase 10 的目标是把当前 60 道 MVP 题库扩充流程，升级为可持续生产、审核和导入
500—1000 道高中题的轻量流水线。

本阶段坚持以下边界：

- 不修改现有训练、推荐、判题和 AI 分析逻辑。
- 不修改 `questions` 表结构。
- 不替换现有 `scripts.import_questions` 和
  `app.services.question_importer.import_questions`。
- JSON 仍是题库交换与导入格式。
- `questions.knowledge_points` 继续保存兼容用中文旧标签。
- 标准知识点以 `knowledge_points.code` 和
  `question_knowledge_points` 为准。
- CLI 负责检查、报告和编排；现有导入器仍是唯一题目写入入口。
- 第一版不建设题库管理后台，不用 LLM 自动决定题目是否合格。

本文是设计方案，暂不包含代码实现。

## 2. 当前能力基线

现有 JSON 导入器已经支持：

- 单题对象、题目数组、`{"questions": [...]}` 三种根结构。
- UTF-8 和 UTF-8 BOM。
- Pydantic 字段与题型校验。
- 选择题选项、答案归一化。
- 难度范围 `1—5`。
- 文件内重复检测。
- 基于规范化题干、选项和答案的 SHA-256 数据库重复检测。
- `question_import_batches` 导入批次日志。
- 部分成功、逐题错误和退出码。

Phase 10 不复制这些规则。质量 CLI 应直接复用：

- `parse_question_json`
- `QuestionImportItem`
- `question_fingerprint`

预检查和正式导入必须使用同一套解析、校验和指纹逻辑，避免“预检查通过、导入失败”的
规则漂移。

## 3. 总体生产流程

```text
题目采集/编写
  ↓
原始 JSON（draft）
  ↓
离线格式检查 lint
  ↓
连接数据库的导入前预检查 precheck
  ├─ 结构与答案检查
  ├─ 重复题检查
  ├─ 标准知识点解析
  ├─ 学科/章节一致性检查
  ├─ 难度和覆盖影响统计
  └─ 生成预检查报告与关联清单
  ↓
人工学科审核
  ↓
批准的 JSON + 冻结 manifest
  ↓
现有 JSON 导入器正式导入
  ↓
按 content_hash 建立 question_knowledge_points
  ↓
导入后 verify
  ↓
题库覆盖/难度报告
  ↓
允许进入训练候选池
```

每批建议控制在 20—50 道。小批次更容易审核、定位问题和安全回滚，不建议直接导入
数百道混合题。

## 4. 文件与批次约定

建议目录：

```text
data/question_bank/
├── drafts/        # 编辑中的原始 JSON
├── approved/      # 人工审核通过、等待导入
├── manifests/     # 预检查冻结清单
└── reports/       # lint、precheck、coverage、difficulty 报告
```

建议文件名：

```text
<subject>_<module>_<batch>_v<version>.json
math_function_batch01_v1.json
physics_kinematics_batch02_v1.json
english_grammar_batch03_v1.json
```

批次 manifest 不进入 `questions` 表，只作为导入证据保存，至少包含：

- 源 JSON 文件名和 SHA-256。
- 预检查时间、数据库版本和映射版本。
- 每题在文件中的 index。
- 与导入器一致的 `content_hash`。
- 标准 primary `knowledge_point_code`。
- 可选 secondary code。
- 检查结果和人工审核状态。
- 审核人、审核时间和备注。

正式导入时必须验证源文件哈希与批准 manifest 一致。文件发生任何修改后必须重新
precheck 和审核。

## 5. JSON 兼容策略

现有 JSON 格式保持不变：

```json
{
  "subject": "数学",
  "chapter": "函数",
  "knowledge_points": ["函数单调性"],
  "difficulty": 3,
  "type": "single_choice",
  "question": "题干",
  "options": ["选项A", "选项B", "选项C", "选项D"],
  "answer": "A",
  "solution": "标准解析",
  "source": "来源"
}
```

Phase 10 不要求在 JSON 中新增数据库字段。标准 code 的输入采用兼容约定：

- 默认从 `knowledge_points` 中的中文名称/别名解析标准 code。
- 对新生产文件，推荐在 `tags` 中增加
  `kp:<KNOWLEDGE_POINT_CODE>`，例如
  `kp:MATH-FUNCTION-MONOTONICITY`。
- `kp:` 只是导入编排元数据，仍写入现有 `tags` JSONB，不改变表结构。
- 如果同时存在中文标签与 `kp:`，二者必须解析到同一节点，否则预检查失败。
- 每题必须有且仅有一个 primary code。
- 第一版不自动推断 secondary；需要 secondary 时必须在 manifest 中人工确认。

知识点解析顺序：

1. 显式 `kp:` code。
2. 当前启用的标准中文名称。
3. 当前启用别名。
4. `kp-mapping-v1.1` redirect。
5. 无唯一结果则失败，禁止自动创建知识点。

`ability_only`、`deprecated`、`redirected` 旧节点不能作为最终 primary。

## 6. 题库质量检查 CLI

建议未来提供统一入口：

```powershell
python -m scripts.question_bank <command> [options]
```

### 6.1 lint：离线质量检查

```powershell
python -m scripts.question_bank lint data/question_bank/drafts/math_batch01.json
```

不连接数据库，检查：

- JSON 可解析且非空。
- 完整复用 `QuestionImportItem`。
- 题型、选项和答案形态正确。
- 必填字段非空。
- 文件内指纹重复。
- 题干、解析、选项中的明显空白和格式问题。
- 单选题是否只有一个可解析答案。
- 多选题答案是否非空、无重复。
- 判断题和简答题是否错误携带选项。
- `solution` 是否仅重复答案、过短或明显缺失推理。
- `source` 是否缺失。
- `knowledge_points` 是否为空或包含重复名称。

离线检查不能确认知识点目录和数据库重复，因此通过 lint 不代表可导入。

### 6.2 precheck：导入前预检查

```powershell
python -m scripts.question_bank precheck `
  data/question_bank/drafts/math_batch01.json `
  --mapping-version kp-mapping-v1.1 `
  --report-dir data/question_bank/reports
```

precheck 只读连接 PostgreSQL，除 lint 外检查：

- 文件内和数据库中是否存在相同 `content_hash`。
- 每个知识点能否唯一解析到启用的三级 code。
- code 学科与题目 `subject` 是否一致。
- code 是否为 `ability_only`、`deprecated` 或 redirect 源。
- 每题是否恰好一个 primary。
- `chapter` 与知识点父级模块是否明显冲突。
- 新批次加入后的知识点覆盖和难度分布。
- 是否触发批次质量门槛。

输出：

- `<batch>.precheck.json`：供工具和 CI 使用。
- `<batch>.precheck.md`：供教师审核。
- `<batch>.manifest.json`：冻结 content hash 与知识点关联。

precheck 不调用现有导入器的写入方法，不创建
`question_import_batches`，不写任何数据库表。

### 6.3 coverage：知识点覆盖统计

```powershell
python -m scripts.question_bank coverage `
  --subjects 数学 物理 英语 `
  --mapping-version kp-mapping-v1.1 `
  --format markdown
```

统计口径默认只包含：

- `questions.is_active=true`
- 有 `question_knowledge_points.role='primary'`
- 目标知识点 `level=3` 且 `is_active=true`

报告维度：

- 学科 → 二级模块 → 三级知识点。
- 总题数、启用题数。
- primary 题数。
- 各难度数量。
- 各题型数量。
- 最近一次新增时间。
- 是否达到最低覆盖目标。
- 无 primary 关联的孤立题目。

同一道题在 primary 覆盖统计中只计入一次。secondary 可单列观察，不参与第一版覆盖
达标判断。

### 6.4 difficulty：难度分布统计

```powershell
python -m scripts.question_bank difficulty --subject 数学
```

按学科、章节、三级知识点输出难度 `1—5` 的数量和比例，并提供：

- 平均难度。
- 中位难度。
- 难度 2—3 的基础训练可用量。
- 低难度或高难度是否断层。
- 样本量过小时“不评价分布”的提示。

难度沿用现有字段：

| 难度 | 生产定义 |
|---:|---|
| 1 | 基础识记或单一步骤，适合建立信心 |
| 2 | 基础概念直接应用，少量计算或辨析 |
| 3 | 常规综合，包含两到三个步骤 |
| 4 | 较强综合或易错变式，需要方法选择 |
| 5 | 高难综合或压轴型，不作为暑假日常训练主体 |

难度由命题人初标、审核人复核。第一版不使用历史正确率自动改写
`questions.difficulty`。

### 6.5 missing：缺失知识点报告

```powershell
python -m scripts.question_bank missing --minimum 5
```

“缺失”分三档：

- `empty`：启用 primary 题数为 0。
- `insufficient`：题数为 1—4。
- `ready`：题数不少于 5。

建议同时输出“达到 10 题还差多少”，用于 500—1000 题阶段排产。报告必须排除
redirected、ability-only 和 deprecated 节点，避免为历史节点继续生产题目。

### 6.6 verify：导入后验证

```powershell
python -m scripts.question_bank verify `
  --manifest data/question_bank/manifests/math_batch01.manifest.json `
  --batch-id 123
```

检查：

- manifest 中每个 content hash 均能找到唯一题目。
- 正式导入数量与批准数量一致。
- 每题有且仅有一个 primary。
- primary code 与 manifest 一致。
- 无跨学科关联。
- 导入器错误和重复记录已被解释。
- 题目加入后的覆盖与难度统计符合 precheck 预览。

verify 失败时，该批次不得宣布完成。

## 7. 质量规则与严重级别

### 7.1 Error：阻止导入

- JSON/Pydantic 校验失败。
- 答案不在选项中或题型与答案形态冲突。
- 文件内重复题。
- 数据库已存在相同题目且批次未明确声明为跳过。
- 无法解析知识点或解析到多个 code。
- 最终 code 不存在、未启用、非三级或学科不一致。
- 使用 ability-only、deprecated 或 redirect 源作为 primary。
- 每题没有 primary 或存在多个 primary。
- 题干、答案或解析为空。
- manifest 与源文件哈希不一致。

### 7.2 Warning：允许进入人工审核，不自动批准

- `source` 为空或来源描述不清。
- 解析过短、只重复正确答案。
- 题干或选项疑似歧义。
- 单个批次难度过度集中。
- 知识点已有大量题，本批次仍继续增加，而缺失节点未覆盖。
- 相似度较高但未达到精确指纹重复。
- 章节名称无法与目录父级稳定对应。

### 7.3 Info：仅统计

- 题型比例。
- 难度比例。
- 本批次对缺失知识点的改善。
- 各知识点距 5 题、10 题目标的差额。

第一版相似题检测可以只报告，不自动删除；精确重复继续使用现有 SHA-256 规则。

## 8. 默认质量门槛

单题必须满足：

- 结构校验通过。
- 正确答案唯一且可判定。
- 有非空标准解析。
- 有且仅有一个有效 primary code。
- 学科一致。
- 无精确重复。

批次建议门槛：

- Error 数必须为 0。
- Warning 必须逐条标记“接受”或“退回”。
- 新增题中难度 2—3 建议占 60%—80%。
- 难度 5 建议不超过 10%。
- 每个批次至少改善一个不足知识点，纯补充已饱和节点需说明理由。
- 每批至少抽查 20%；首批和新来源建议 100% 人工审核。

这些比例是暑假 MVP 的生产基线，应作为配置而非写死在训练逻辑中。

## 9. 知识点覆盖统计设计

### 9.1 核心指标

| 指标 | 定义 |
|---|---|
| `primary_question_count` | 该知识点作为 primary 的启用题数 |
| `secondary_question_count` | 该知识点作为 secondary 的启用题数 |
| `difficulty_counts` | 难度 1—5 数量 |
| `type_counts` | 各题型数量 |
| `coverage_status` | empty / insufficient / ready |
| `gap_to_5` | 距离 5 题的缺口 |
| `gap_to_10` | 距离 10 题的缺口 |
| `unlinked_question_count` | 没有 primary 的启用题数 |

### 9.2 第一阶段排产顺序

1. `empty` 节点。
2. 只有 1—2 题的节点。
3. 难度 2—3 缺失的节点。
4. 与学生低掌握度或近期错误相关的节点。
5. 已有 10 题以上的节点暂缓扩充。

排产可以参考学习画像，但题库质量检查本身不修改推荐算法。

## 10. 导入前预检查报告结构

机器可读 JSON 建议结构：

```json
{
  "schema_version": "question-bank-precheck-v1",
  "mapping_version": "kp-mapping-v1.1",
  "source_file": "math_function_batch01_v1.json",
  "source_sha256": "...",
  "database_revision": "20260723_0010",
  "summary": {
    "total": 20,
    "passed": 20,
    "errors": 0,
    "warnings": 2,
    "file_duplicates": 0,
    "database_duplicates": 0
  },
  "items": [
    {
      "index": 1,
      "content_hash": "...",
      "subject": "数学",
      "chapter": "函数",
      "primary_code": "MATH-FUNCTION-MONOTONICITY",
      "difficulty": 2,
      "errors": [],
      "warnings": []
    }
  ],
  "coverage_delta": {},
  "difficulty_delta": {}
}
```

Markdown 报告面向审核人员，应突出：

- 阻断问题。
- 需要人工判断的问题。
- 每题 primary 预览。
- 重复题详情。
- 覆盖变化。
- 难度变化。
- 最终“允许导入/禁止导入”结论。

## 11. 正式导入与标准关联

正式导入继续调用：

```powershell
python -m scripts.import_questions data/question_bank/approved/math_batch01_v1.json
```

导入后标准关联不能依赖新生成的题目 ID，也不能修改现有导入器的指纹规则。建议流程：

1. precheck 用现有 `question_fingerprint` 冻结每题 `content_hash → primary_code`。
2. 现有导入器写入 `questions`。
3. 后置关联命令按 `content_hash` 查询真实 `question_id`。
4. 写入 `question_knowledge_points`，使用现有
   `(question_id, knowledge_point_id)` 唯一约束和每题唯一 primary 索引。
5. 已存在且完全一致则跳过；冲突则整批失败回滚。
6. verify 确认导入批次与关联清单完整一致。

后置关联是 Phase 10 的编排能力，不改变训练服务。任何未建立 primary 的新题都应在
verify 报告中视为 Error，不应进入正式训练。

## 12. 人工审核流程

每批至少经过两个角色：

### 命题/整理人

- 保证题干、答案、解析和来源完整。
- 初标学科、章节、知识点和难度。
- 处理 lint 和 precheck 错误。

### 学科审核人

- 独立作答并确认唯一正确答案。
- 检查解析是否能让高中生理解。
- 确认知识点 code 和难度。
- 检查是否符合青海高中教学与高考复习场景。
- 对 warning 作出接受或退回决定。

AI 生成题必须标记来源，且与人工收集题使用同一检查和审核门槛。AI 不得直接写数据库，
不得自行批准知识点或答案。

## 13. 失败处理与可恢复性

- lint/precheck 失败：只修改 draft，重新执行，不影响数据库。
- 正式导入部分失败：根据 `question_import_batches` 定位；不得忽略失败项后直接宣布完成。
- 题目已导入但关联失败：保留导入日志，修复 manifest 或冲突后重跑关联；verify 前不得使用。
- 发现错误答案：停用相关题目，先评估已有答题记录影响，不直接删除题目。
- 发现错误知识点关联：通过单独、可审计的数据修订处理，不修改题目 ID。
- 批次文件、manifest、报告和导入结果必须一同留档。

## 14. 建议开发顺序

### Phase 10.1：只读质量 CLI

- `lint`
- `coverage`
- `difficulty`
- `missing`
- JSON/Markdown 报告

不写数据库，风险最低。

### Phase 10.2：导入前预检查

- 数据库重复检查
- 标准 code 解析
- 覆盖/难度增量预览
- manifest 冻结
- CI 退出码

仍不写数据库。

### Phase 10.3：受控导入编排

- 校验批准文件哈希
- 调用现有 JSON 导入器
- 根据 content hash 建立标准关联
- 导入后 verify

不改变导入器的核心数据校验和题目写入逻辑。

### Phase 10.4：批量生产与质量回顾

- 每批 20—50 题扩充。
- 优先补齐 empty/insufficient 节点。
- 每累计约 100 题复核难度和题型分布。
- 达到 500 题后再评估是否需要简单审核后台。

## 15. 验收标准

Phase 10 完成时应满足：

- 同一 JSON 使用预检查与现有导入器得到一致校验结果。
- precheck 不产生数据库写入。
- 精确重复不会进入正式题库。
- 每道新题都有唯一、有效、同学科的 primary。
- coverage 能覆盖全部启用三级知识点。
- difficulty 能按学科、章节、知识点统计 1—5 级分布。
- missing 能稳定列出 0 题、少于 5 题和距 10 题缺口。
- 正式导入有源文件、manifest、人工审核、导入批次和 verify 五类证据。
- 新题加入后，现有每日训练和专项训练回归测试保持通过。
