# AI 学习助手 MVP 项目方案

## 1. 项目目标

### 1.1 产品定位

面向青海西宁准高三学生的 27 天暑假学习助手，通过每日少量、持续、可反馈的训练，帮助学生发现薄弱知识点、理解错因并形成稳定的学习节奏。

MVP 的核心闭环是：

> 每日 6 题训练 → 提交答案 → 客观判题 → AI 错题分析 → 记录知识点掌握情况 → 推荐下一批题目

### 1.2 MVP 目标

- 学生每天能够在 15～30 分钟内完成 6 道题。
- 系统能够保存作答过程、结果和错题，并展示 27 天学习进度。
- 客观题由规则引擎判题，错误题目由 LLM 生成易懂、可执行的错题分析。
- 系统根据近期正确率、知识点薄弱度和题目难度生成次日训练内容。
- 教学内容与青海高考实际使用的教材版本、考试科目和新高考政策保持一致；正式录题前必须由当地教师确认。

### 1.3 MVP 范围

包含：

- 手机号或账号登录、学生基本资料与科目选择。
- 27 天学习计划和每日 6 题任务。
- 单选、多选、判断、填空/简答等基础题型。
- 作答、判题、答案解析和 AI 错题分析。
- 学习日历、正确率、连续学习天数、知识点掌握度。
- 基于规则的个性化推荐，LLM 仅参与解释，不直接决定推荐结果。
- 题目、答案和知识点的后台导入及基础管理能力。

暂不包含：

- AI 自动出题、拍照搜题、语音对话和作文批改。
- 复杂社交、排行榜、家长端和教师端完整产品。
- 自适应测评算法、知识图谱推理和精细化心理画像。
- 付费、营销、优惠券等商业化能力。

### 1.4 成功指标

- 激活率：注册后 24 小时内完成首个任务的用户比例。
- 首周留存：第 7 天仍完成任务的用户比例。
- 任务完成率：已生成任务中完成 6 题的比例。
- 27 天完成率：完成不少于 22 天训练的用户比例。
- 错题复练提升：同知识点复练正确率相对首次正确率的变化。
- AI 分析质量：有用反馈率、重新生成率、平均响应时间和失败率。

## 2. 用户场景

### 2.1 核心用户

主要用户是青海西宁即将进入高三、希望利用暑假查漏补缺的学生。典型特点包括：可支配学习时间有限、学科基础差异较大、主要使用手机、需要明确且负担较低的每日任务。

### 2.2 核心使用流程

#### 首次使用

1. 学生注册并选择年级、选考组合、目标科目和自评水平。
2. 系统展示 27 天计划、每日预计用时和训练规则。
3. 首日采用覆盖基础知识点的 6 题作为轻量诊断。
4. 完成后生成首份学习反馈，并建立初始知识点掌握度。

#### 每日训练

1. 学生进入首页，看到“第 N/27 天”、连续学习天数和今日 6 题。
2. 学生逐题作答，可暂存进度；提交后客观题立即判定。
3. 错题优先显示标准解析，随后异步生成 AI 错因分析和改进建议。
4. 完成 6 题后展示正确率、薄弱知识点和明日建议。
5. 推荐服务根据最新记录生成下一日任务，必要时安排错题变式或同知识点复练。

#### 学习复盘

1. 学生从学习记录查看日历、每日完成情况和正确率趋势。
2. 按学科、知识点或错误类型筛选错题。
3. 对薄弱知识点发起复练，系统记录复练后的变化。

### 2.3 异常场景

- 网络中断：答案先保存在客户端，恢复后幂等提交。
- 当日未完成：任务保留，次日允许补做，但不无限累积每日任务。
- LLM 超时或不可用：先返回规则判题与人工解析，AI 分析进入队列重试。
- AI 分析不合适：允许反馈“无帮助/有错误”并重新生成一次，原结果保留供审计。
- 题目或答案有误：提供报错入口，题目下线后不影响历史作答记录。

## 3. 技术架构

### 3.1 总体方案

MVP 采用“模块化单体 + 异步任务”的结构，避免早期微服务带来的部署和数据一致性成本，同时为后续拆分保留明确边界。

```text
Web/H5 客户端
      │ HTTPS / JSON
      ▼
FastAPI 应用
├── 用户与认证模块
├── 题库与知识点模块
├── 27 天计划/每日任务模块
├── 作答与判题模块
├── 学习记录与统计模块
├── 推荐服务（确定性规则）
└── AI 分析服务（Provider 适配层）
      │                 │
      ▼                 ▼
PostgreSQL          任务队列/Worker ── LLM API
                         │
                         ▼
                    Redis（队列、限流、短期缓存）
```

### 3.2 后端分层

```text
app/
├── api/             # 路由聚合、依赖注入、鉴权
├── routers/         # HTTP 请求与响应，不承载业务规则
├── schemas/         # Pydantic 输入输出契约
├── models/          # SQLAlchemy 数据模型
├── repositories/    # 数据访问与查询封装
├── services/        # 训练、判题、统计、推荐等业务逻辑
├── ai/              # LLM Provider、Prompt 版本与结构化输出
├── workers/         # AI 分析等异步任务
├── core/            # 配置、安全、日志、异常和可观测性
└── db/              # 会话、迁移和种子数据
```

### 3.3 技术选型

| 领域 | MVP 选型 | 说明 |
|---|---|---|
| API | FastAPI + Pydantic | OpenAPI 契约清晰，适合异步 I/O |
| ORM/迁移 | SQLAlchemy 2.x + Alembic | 异步会话，迁移可审计 |
| 数据库 | PostgreSQL 16 | 事务、JSONB、索引与统计能力成熟 |
| 缓存/队列 | Redis + 轻量任务 Worker | AI 请求异步化、重试、限流；规模扩大后可替换 Celery 等方案 |
| 鉴权 | 短期 Access Token + Refresh Token | Refresh Token 哈希存库并支持撤销 |
| LLM | Provider Adapter + 结构化 JSON 输出 | 隔离供应商，支持超时、降级、重试和成本统计 |
| 测试 | pytest + httpx + Testcontainers | 覆盖服务、API 和 PostgreSQL 集成测试 |
| 部署 | Docker + 托管 PostgreSQL/Redis | API 与 Worker 独立进程，开发/预发/生产隔离 |

### 3.4 关键设计决策

- 判题与 AI 解耦：确定答案的题型必须由规则引擎判题，LLM 只解释错因，避免幻觉影响正确性。
- AI 异步生成：提交答案立即返回判题结果，AI 分析状态为 `pending`；客户端轮询或使用 SSE 获取完成结果。
- Prompt 可追踪：每条 AI 分析保存模型、Prompt 版本、耗时、Token 用量和状态，以便审计和优化。
- 推荐先规则化：按“错题复练 > 薄弱知识点 > 当期重点 > 难度适配 > 去重”生成 6 题，结果需可解释、可复现。
- 每日任务快照：任务创建后保存题目版本与顺序，题库后续修改不能改变学生已经看到的任务。
- 数据最小化：不收集与学习无关的未成年人信息；日志不得记录密码、Token 或完整个人信息。
- 幂等性：任务生成和答案提交使用唯一约束或幂等键，防止重复任务和重复记录。

### 3.5 非功能要求

- 常规 API P95 响应时间小于 500ms；AI 分析异步完成目标小于 15 秒。
- API 和 Worker 可水平扩容；服务保持无状态。
- 数据库每日备份，关键表支持时间点恢复；迁移必须可回滚或提供前向修复方案。
- 使用结构化日志和请求 ID，监控请求错误率、数据库连接池、队列积压、LLM 延迟与费用。
- 针对登录、提交答案和 AI 分析实施用户级/IP 级限流。

## 4. API 设计

统一前缀为 `/api/v1`，使用 JSON；列表接口统一游标或页码分页。错误响应至少包含 `code`、`message`、`request_id`。所有时间使用 UTC 存储，响应使用 ISO 8601。

### 4.1 认证与用户

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/auth/register` | 注册账号 | 否 |
| POST | `/auth/login` | 登录并签发 Token | 否 |
| POST | `/auth/refresh` | 刷新 Access Token | Refresh Token |
| POST | `/auth/logout` | 撤销当前 Refresh Token | 是 |
| GET | `/users/me` | 获取个人资料 | 是 |
| PATCH | `/users/me` | 更新年级、科目、学习目标等 | 是 |

### 4.2 学习计划和每日任务

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/plans` | 创建 27 天计划；同一用户只允许一个进行中计划 | 是 |
| GET | `/plans/current` | 获取当前计划及总体进度 | 是 |
| GET | `/daily-tasks/today` | 获取今日任务，不存在时幂等生成 6 题 | 是 |
| GET | `/daily-tasks/{task_id}` | 获取指定任务及题目快照 | 是 |
| POST | `/daily-tasks/{task_id}/complete` | 完成任务并生成总结 | 是 |

今日任务响应不返回标准答案和完整解析。每个题目包含题型、题干、选项、知识点概要和序号。

### 4.3 题目与作答

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/daily-tasks/{task_id}/answers` | 提交单题答案，支持 `Idempotency-Key` | 是 |
| GET | `/answers/{answer_id}` | 获取判题结果、标准解析和 AI 状态 | 是 |
| GET | `/answers/{answer_id}/analysis` | 获取 AI 错题分析；处理中返回 202 | 是 |
| POST | `/answers/{answer_id}/analysis/retry` | 对失败或低质量分析重试一次 | 是 |
| POST | `/answers/{answer_id}/feedback` | 反馈 AI 分析是否有帮助 | 是 |

提交答案请求示例：

```json
{
  "task_item_id": "uuid",
  "answer": {"selected": ["B"]},
  "duration_seconds": 83
}
```

提交答案响应示例：

```json
{
  "answer_id": "uuid",
  "is_correct": false,
  "correct_answer": {"selected": ["C"]},
  "explanation": "题库中的人工标准解析",
  "ai_analysis": {"status": "pending"}
}
```

### 4.4 学习记录与推荐

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/learning-records/overview` | 27 天完成度、连续天数和总体正确率 | 是 |
| GET | `/learning-records/calendar` | 每日完成情况 | 是 |
| GET | `/learning-records/knowledge-points` | 各知识点掌握度与趋势 | 是 |
| GET | `/learning-records/wrong-answers` | 错题分页列表和筛选 | 是 |
| GET | `/recommendations/next` | 查看下一任务的推荐理由预览 | 是 |

### 4.5 内容管理

MVP 可先提供受管理员权限保护的接口或内部脚本：

- `POST /admin/questions/import`：批量导入经审核题目。
- `POST /admin/questions`、`PATCH /admin/questions/{id}`：维护题目和版本。
- `POST /admin/questions/{id}/publish`：审核发布。
- `GET /admin/question-issues`：查看学生报错。

管理员接口必须采用角色权限控制，并记录审计日志。

## 5. 数据库设计

所有业务主键建议使用 UUID；表均包含 `created_at`、`updated_at`。需要保留历史的记录采用状态变更或软删除，不直接物理删除。

### 5.1 核心关系

```text
users 1 ── N refresh_tokens
users 1 ── N study_plans 1 ── N daily_tasks 1 ── 6 daily_task_items
subjects 1 ── N questions N ── N knowledge_points
questions 1 ── N question_versions
daily_task_items N ── 1 question_versions
daily_task_items 1 ── 0..N answer_records 1 ── 0..1 ai_analyses
users 1 ── N knowledge_masteries N ── 1 knowledge_points
```

### 5.2 表设计

#### `users`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | 用户 ID |
| username | varchar(50) unique | 登录名；若使用手机号，另设加密字段及查询哈希 |
| password_hash | varchar(255) | Argon2 哈希 |
| grade | smallint | 当前年级 |
| city | varchar(50) | 默认西宁，非必填 |
| selected_subjects | jsonb | 选考组合/训练科目 |
| target_score | jsonb | 各科目标分，非必填 |
| status | varchar(20) | active/disabled |

#### `refresh_tokens`

保存 `user_id`、Token 哈希、过期时间、撤销时间、设备信息。只保存哈希，不保存明文 Token。

#### `subjects` 与 `knowledge_points`

- `subjects`：学科代码、名称、是否启用。
- `knowledge_points`：所属学科、名称、父知识点、教材/考纲版本、排序和状态。
- 父子关系支持章节层级；首期不实现复杂图关系。

#### `questions` 与 `question_versions`

`questions` 保存稳定 ID、学科和当前发布版本；`question_versions` 保存：

- `question_id`、版本号、题型、题干和选项 JSONB。
- 标准答案 JSONB、人工解析、难度（1～5）、来源和适用地区。
- 审核状态 `draft/review/published/retired`、审核人和发布时间。
- 题目内容使用版本表，保证历史任务可重放。

通过 `question_knowledge_points(question_id, knowledge_point_id, weight)` 建立题目与知识点多对多关系。

#### `study_plans`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | 计划 ID |
| user_id | uuid FK | 学生 |
| start_date/end_date | date | 固定 27 天窗口 |
| total_days | smallint | 默认 27 |
| questions_per_day | smallint | 默认 6 |
| status | varchar(20) | active/completed/abandoned |

约束：每个用户最多存在一个 `active` 计划，可使用部分唯一索引实现。

#### `daily_tasks` 与 `daily_task_items`

- `daily_tasks`：所属计划、计划第几天、训练日期、状态、完成时间、推荐策略版本。
- 唯一约束：`(study_plan_id, day_number)`。
- `daily_task_items`：任务、题目版本、顺序、推荐原因、题目快照哈希。
- 唯一约束：`(daily_task_id, position)`；应用层和数据库约束共同确保每天恰好 6 个有效题目。

#### `answer_records`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | 作答 ID |
| user_id/task_item_id | uuid FK | 用户与任务题目 |
| attempt_no | smallint | 第几次作答 |
| submitted_answer | jsonb | 统一承载各题型答案 |
| is_correct | boolean | 规则判题结果 |
| duration_seconds | integer | 作答用时 |
| error_type | varchar(30) | 概念/计算/审题/未知等，可后续确认 |
| submitted_at | timestamptz | 提交时间 |
| idempotency_key | varchar(64) | 防重复提交 |

唯一约束：`(user_id, idempotency_key)`。历史作答永不随题目修改而覆盖。

#### `ai_analyses`

保存 `answer_record_id`、状态、模型供应商、模型名、Prompt 版本、结构化结果 JSONB、失败原因、Token 用量、费用估算、耗时和重试次数。

结构化结果至少包含：

- `error_summary`：本题主要错因。
- `reasoning_steps`：正确思路，限制步骤和长度。
- `knowledge_gaps`：关联知识点。
- `next_action`：学生下一步可执行建议。
- `safety_flags`：内容安全或低置信标记。

#### `knowledge_masteries`

按用户和知识点保存 `attempt_count`、`correct_count`、近期正确率、掌握分（0～100）、最后练习时间和计算版本。唯一约束为 `(user_id, knowledge_point_id)`。

掌握分在提交答案事务后由确定性算法更新；原始作答是事实来源，该表是可重算的派生数据。

#### `recommendation_logs`

记录每次推荐的用户、候选题、最终题目、规则版本和理由。该表用于排查“为什么推荐这道题”，不依赖 LLM。

### 5.3 关键索引

- `daily_tasks(study_plan_id, day_number)` 唯一索引。
- `answer_records(user_id, submitted_at desc)` 学习记录查询索引。
- `answer_records(task_item_id, attempt_no)` 唯一索引。
- `knowledge_masteries(user_id, mastery_score, last_practiced_at)` 薄弱点推荐索引。
- `question_versions(status, subject_id, difficulty)` 候选题筛选索引。
- `question_knowledge_points(knowledge_point_id, question_id)` 知识点反查索引。
- `ai_analyses(status, created_at)` Worker 扫描与补偿索引。

## 6. 两周开发计划

团队假设：2 名后端、1 名前端、1 名产品/设计、1 名兼职教研与测试。若只有 1 名全栈开发，应将管理后台和 AI 反馈延后，优先保证每日训练闭环。

### 第一周：打通无 AI 的核心闭环

| 天 | 目标 | 主要交付物 |
|---|---|---|
| Day 1 | 需求冻结与工程初始化 | 用户故事、验收标准、OpenAPI 草案、FastAPI/PostgreSQL/迁移/日志/CI 基线 |
| Day 2 | 用户与内容基础 | 注册登录、Token 刷新、用户资料；学科、知识点和题目模型 |
| Day 3 | 题库与导入 | 题目版本、审核状态、批量导入脚本；首批题目校验规则 |
| Day 4 | 27 天计划与任务 | 创建计划、今日任务幂等生成、6 题快照、任务读取接口 |
| Day 5 | 作答与判题 | 多题型答案结构、规则判题、幂等提交、答案解析、单元测试 |
| Day 6 | 学习记录 | 完成度、正确率、日历和知识点掌握度；数据库集成测试 |
| Day 7 | 联调与里程碑验收 | H5 完成“登录—6 题—结果—记录”闭环，修复阻断问题 |

第一周退出条件：关闭 LLM 也能完成完整训练；题目答案不泄漏；重复请求不会产生重复作答；核心接口集成测试通过。

### 第二周：AI、推荐和上线准备

| 天 | 目标 | 主要交付物 |
|---|---|---|
| Day 8 | AI 服务边界 | LLM Provider、结构化 Schema、Prompt v1、超时/重试/降级、Mock 测试 |
| Day 9 | 异步错题分析 | Redis 队列与 Worker、状态查询、失败补偿、Token 和费用记录 |
| Day 10 | 推荐 v1 | 薄弱知识点、错题复练、难度和去重规则；推荐日志与离线样例测试 |
| Day 11 | 用户反馈与风控 | AI 有用性反馈、内容安全检查、频率限制、敏感日志清理 |
| Day 12 | 质量与性能 | 端到端测试、并发提交测试、慢查询检查、LLM 故障演练 |
| Day 13 | 预发布与教研验收 | 预发部署、数据库备份恢复演练、教师抽检题目和 AI 分析 |
| Day 14 | 小范围试运行 | 10～30 名学生灰度、监控看板、问题分级、上线/回滚检查清单 |

第二周退出条件：LLM 不可用时训练主流程仍正常；推荐结果可解释；关键指标和告警可见；教研抽检通过；具备回滚和数据恢复方案。

### 6.1 测试重点

- 判题规则：每种题型的正确、错误、空答案、乱序多选和异常输入。
- 数据隔离：用户不能读取其他用户的任务、答案或学习记录。
- 幂等与并发：重复生成今日任务、重复提交、同时完成任务。
- 内容安全：接口不提前暴露答案，日志不包含凭证，AI 输出经过 Schema 与安全校验。
- 降级：Redis、LLM 或 Worker 不可用时，判题和学习记录仍可用。
- 时间边界：西宁使用中国标准时间展示，数据库 UTC 存储；跨日、补做和第 27 天结束逻辑明确。

### 6.2 主要风险与应对

| 风险 | 影响 | MVP 应对 |
|---|---|---|
| 本地教材、选科和考纲确认不足 | 题目不适用，产品价值失真 | 开发首日锁定学科范围，由西宁一线教师确认内容标准 |
| 高质量题库不足或版权不清 | 无法稳定提供每日训练 | 仅使用自有/获授权题目，保留来源和授权信息，先聚焦 1～2 科 |
| LLM 幻觉或错误讲解 | 误导学生 | 规则判题、人工标准解析优先；LLM 只解释并展示 AI 标识，支持反馈和下线 |
| 两周范围过大 | 核心闭环延期 | P0 只保留登录、任务、作答、记录、错题分析；后台先用导入脚本 |
| 推荐冷启动 | 首日推荐不准 | 首日基础诊断 + 年级/科目默认路径；数据不足时使用教研规则 |
| 未成年人隐私与内容安全 | 合规和信任风险 | 最小收集、加密传输、权限隔离、隐私告知、数据删除机制；上线前进行合规审查 |
| LLM 延迟、限流和成本失控 | 体验下降、费用超预算 | 异步队列、超时降级、每日配额、缓存相同题型模板、费用告警 |
| 27 天留存不足 | 无法达成学习目标 | 每日任务保持 6 题和明确用时，提供进度反馈与温和提醒，不用惩罚性机制 |

## 7. MVP 验收定义

- 新用户可在 3 分钟内完成注册、创建计划并开始首日任务。
- 每个有效学习日稳定生成 6 道不重复且符合科目配置的题目。
- 答案提交幂等，客观题判题结果与测试用例完全一致。
- 错题立即显示人工解析，AI 分析失败不阻塞任务完成。
- 用户可查看 27 天进度、每日记录、错题和知识点薄弱度。
- 推荐的每道题都有可查询的确定性推荐理由。
- 管理员可导入、审核和下线题目，历史数据保持不变。
- 预发布环境通过安全、数据隔离、备份恢复和关键故障降级检查。
