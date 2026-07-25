# AI Study Backend

面向准高三学生的 FastAPI 学习助手后端，包含用户、题库、每日 6 题任务、答题记录、知识掌握度和 AI 错题分析。

## 本地启动

```powershell
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
Copy-Item .env.example .env
.venv\Scripts\alembic upgrade head
.venv\Scripts\uvicorn app.main:app --reload
```

Swagger：`http://127.0.0.1:8000/docs`；健康检查：`GET /health`。

主要接口位于 `/api/v1`：

- `/users`：注册、登录和个人资料
- `/questions`：题库分页查询和维护
- `/daily-tasks`：每日 6 题任务
- `/student-answers`：提交答案、历史和统计
- `/knowledge-status`：个人知识点掌握度
- `/student-answers/{answer_id}/analysis`：读取结构化错题分析状态和结果
- `/student-answers/{answer_id}/feedback`：保存学生主观难度反馈

LLM 调用全部集中在 `app/services/llm.py`。在 `.env` 中设置 `LLM_ENABLED=true`、
`LLM_API_KEY`、`LLM_MODEL` 和 OpenAI 兼容的 `LLM_BASE_URL` 后启用。前端不会提交
正确答案、知识点或提示词；这些信息均由后端根据 `answer_id` 查询并构造。

生产环境必须修改 `SECRET_KEY` 和 PostgreSQL `DATABASE_URL`。

## 题库初始化

题库通过项目内 CLI 导入，不对学生账号开放批量写入接口。首次导入前先执行迁移：

```powershell
E:\1a\.venv\Scripts\alembic.exe upgrade head
```

导入三科示例题库：

```powershell
E:\1a\.venv\Scripts\python.exe -m scripts.import_questions `
  data/questions/math.json `
  data/questions/physics.json `
  data/questions/english.json
```

每个文件可以是单个题目对象、题目数组，或 `{ "questions": [...] }`。单题格式：

```json
{
  "subject": "数学",
  "chapter": "函数",
  "knowledge_points": ["函数单调性"],
  "difficulty": 3,
  "type": "single_choice",
  "question": "题干",
  "options": ["选项 A", "选项 B"],
  "answer": "A",
  "solution": "标准解析",
  "source": "题目来源"
}
```

选择题的 `answer` 可以使用 `A/B/C/D`，也可以直接填写完整选项；导入时会转换成
规则判题所使用的完整选项值。系统会校验字段、题型、选项和答案，并使用规范化内容的
SHA-256 指纹检测文件内及数据库中的重复题。

每次导入都会写入 `question_import_batches`，保存文件哈希、成功数、重复数、失败数和
逐条错误详情。CLI 同时输出 JSON 汇总；存在格式错误时退出码为 1，仅有重复题时仍会
正常完成并在结果中列明。

审核题库正式发布必须使用事务化编排命令。该命令在同一事务中写入题目和标准 primary
知识点关联，冲突时自动回滚；`--dry-run` 只生成导入前报告：

```powershell
E:\1a\.venv\Scripts\python.exe -m scripts.release_questions `
  phase10_3_final_candidate_v2.json `
  --dry-run

E:\1a\.venv\Scripts\python.exe -m scripts.release_questions `
  phase10_3_final_candidate_v2.json
```

报告默认写入 `data/question_bank/reports/`。正式导入保留
`question_import_batches` 批次记录，并验证导入前题目未变化、每道新题恰好具有一个
有效的 primary 知识点关联。重复执行时，已存在且关联一致的题目会安全跳过；关联冲突
则整批失败。

恢复时优先把导入前的 `pg_dump` 恢复到替代数据库并完成验证后切换。若新题尚未产生
答题、每日任务或训练记录，也可以根据发布报告中的题目 ID，在一个经过审计的事务内
同时删除其知识点关联和题目。仅删除 `question_import_batches` 记录不能恢复题目数据；
一旦新题已有业务引用，应停用并评估影响，不应直接删除。

## Phase 11.1：错题本

错题本直接聚合现有 `student_answers`，不复制答题数据，也不新增数据库表：

- `GET /api/v1/wrong-questions`：返回当前用户按题目聚合的历史错题。
- 支持 `subject`、`knowledge_point_code`、`sort`、`page`、`page_size`。
- `sort=error_count_desc` 按错误次数优先，`sort=recent_desc` 按最近错误优先。
- 每项包含最近一次错误答案、正确答案、标准解析、AI分析状态、AI分析结果、最近错误时间和累计错误次数。
- `POST /api/v1/wrong-questions/{question_id}/practice`：仅允许重练当前用户确实答错过的题，创建单题 `wrong_review` 训练会话。

错题重练继续复用 `training_sessions`、统一判题、AI错题分析和知识掌握度更新流程。
移动端入口为底部导航“错题”，支持学科、标准知识点筛选和展开复盘。AI分析失败不会
阻断标准解析显示。

## Phase 11.2：专项训练增强

专项训练复用现有 `training_sessions`，不新增数据库表：

- `GET /api/v1/training-sessions/subject/catalog`：通过
  `question_knowledge_points` 返回标准三级知识点code、名称、题量和1—5级难度分布。
- `POST /api/v1/training-sessions/subject`：支持 `subject`、`chapter`、
  `knowledge_point_code`、`difficulty` 和 `question_count`。
- 旧的 `knowledge_point` 名称参数暂时保留兼容，新客户端使用稳定code。
- 训练会话使用 `selection_version=subject-v2`，并在 `selection_config` 中记录标准code
  和指定难度。

移动端专项训练页面可依次选择学科、章节、标准知识点、难度和题量。提交答案仍走统一
`student_answers`、规则判题、AI错题分析和知识掌握度更新链路。

示例数据位于 `data/questions/`，数学、物理、英语各 20 题，仅用于 MVP 流程验证，
正式用户测试前应由当地教师复核内容与教材适配性。

## Phase 10.1：题库质量检查 CLI

题库质量工具只执行文件读取和数据库查询，不会导入、更新或删除题目。安装项目后使用：

```powershell
question_bank lint data/questions/math.json
question_bank coverage --subject 数学
question_bank difficulty --subject 物理
question_bank missing --subject 英语 --minimum 5
question_bank verify
```

也可以直接通过模块运行：

```powershell
E:\1a\.venv\Scripts\python.exe -m app.cli.question_bank lint data/questions/math.json
```

命令职责：

- `lint`：复用现有 JSON 解析、Pydantic 校验和题目指纹，检查格式、答案、文件内重复和基础质量。
- `coverage`：按启用的标准三级知识点统计 primary 题量、难度和题型。
- `difficulty`：输出难度 1—5 数量、平均难度及逐知识点分布。
- `missing`：输出 0 题或低于指定题量的标准知识点。
- `verify`：不带文件时检查正式题库 primary 完整性；带 JSON 文件时执行数据库感知的导入前
  预检查，包括标准 code、学科一致性和数据库重复检测。

所有命令默认输出 JSON。使用 `--report path.json` 或 `--report path.md` 保存机器可读或
人工审核报告。发现阻断错误时退出码为 1。历史 redirected 节点和 ability-only 节点不会
进入覆盖率或缺失知识点统计。

详细生产流程见 `docs/QUESTION_BANK_PIPELINE.md`。

## 每日 6 题自动生成

登录用户请求 `GET /api/v1/daily-tasks/today` 时，系统会幂等地读取或生成当天任务：

- 默认学科配额：英语 3 题、物理 2 题、数学 1 题。
- 某学科题量不足时，按英语、物理、数学、化学、生物的优先顺序补齐。
- 知识点掌握度越低，题目排序越靠前。
- 最近答错知识点优先复练。
- 掌握度未知时优先难度 2～3；近期错误率不低于 50% 时优先难度 1～2；
  同一学科连续答对至少 3 题时优先难度 3～4。
- 严格排除最近 7 天已经作答的题目。
- 同一任务不会出现重复题；用户和日期唯一约束保证并发请求只生成一个任务。
- 推荐策略完全基于规则，不调用 LLM。

验证前确保迁移和示例题已导入：

```powershell
E:\1a\.venv\Scripts\alembic.exe upgrade head
E:\1a\.venv\Scripts\python.exe -m scripts.import_questions `
  data/questions/math.json data/questions/physics.json data/questions/english.json
```

启动 API、注册或登录后，携带 Access Token 请求：

```powershell
$headers = @{ Authorization = "Bearer YOUR_ACCESS_TOKEN" }
$first = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/daily-tasks/today" `
  -Headers $headers
$second = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/daily-tasks/today" `
  -Headers $headers

$first.items | Select-Object position, recommendation_reason,
  @{N='subject';E={$_.question.subject}},
  @{N='difficulty';E={$_.question.difficulty}}
"same task: $($first.id -eq $second.id)"
```

预期结果为 6 个不同题目，首次请求生成任务，第二次请求返回相同任务 ID。

## AI 错题分析与学习反馈

提交答案仍使用 `POST /api/v1/student-answers`。规则判题和标准解析会立即返回：

- 正确答案的 `analysis_status` 为 `not_requested`，不会调用 LLM。
- 错误答案的 `analysis_status` 为 `pending`，后端使用轻量后台任务调用一次 LLM。
- AI 失败或未配置时，答题记录和标准解析不受影响，状态更新为 `failed`。
- AI 成功时结果写入 `student_answers.ai_analysis`，状态更新为 `completed`。

前端通过以下接口读取结果，不需要传递任何 AI 上下文：

```text
GET /api/v1/student-answers/{answer_id}/analysis
```

结构化结果包含：

```json
{
  "mistake_type": "概念理解错误",
  "reason": "错误原因",
  "knowledge_gap": "函数单调性",
  "suggestion": "下一步学习建议",
  "next_training": "建议继续训练方向"
}
```

`mistake_type` 仅允许概念理解错误、计算错误、审题错误、方法选择错误、知识记忆错误
和其他。`knowledge_gap` 会规范到题目已有知识点，并增加对应
`knowledge_status.ai_gap_count`。掌握度采用基础正确率减去 AI 漏洞惩罚，惩罚上限为 20 分。

学生可以在答题后提交可选反馈：

```http
PATCH /api/v1/student-answers/{answer_id}/feedback
Content-Type: application/json

{"difficulty_feedback":"difficult"}
```

允许值为 `easy`、`difficult`、`dont_know`。阶段三只保存事实数据，不直接用主观反馈
修改掌握度。

## 移动端前端

```powershell
Set-Location frontend
npm install
npm run dev
```

前端使用 Vue 3、Vite 和 Tailwind CSS，默认通过 Vite 将 `/api` 代理到
`http://127.0.0.1:8000`。生产部署时通过 `VITE_API_BASE_URL` 指定 API 地址。

### 每日任务状态恢复

前端加载今日任务后，通过以下接口恢复该任务已经提交的答案：

```http
GET /api/v1/daily-tasks/{task_id}/answers
Authorization: Bearer ACCESS_TOKEN
```

接口仅返回当前用户在该任务中已经作答的题目，并包含学生答案、判题结果、正确答案、
标准解析、AI 分析状态和难度反馈。未作答题目不会返回正确答案。刷新页面或重新登录后，
学生可以直接查看原作答结果并从下一道未完成题继续。

完成任务仍使用：

```http
POST /api/v1/daily-tasks/{task_id}/complete
```

后端会验证当前用户已经完成任务内全部 6 个题目；未完成时返回 `409`，前端不能直接
把任务标记为完成。移动端的今日日期、问候语和近 7 天统计统一使用
`Asia/Shanghai` 时区。

验证命令：

```powershell
E:\1a\.venv\Scripts\ruff.exe check app tests alembic\versions
E:\1a\.venv\Scripts\pytest.exe -q
Set-Location E:\1a\frontend
npm run typecheck
npm run build
```

## Android 局域网测试

电脑和手机连接同一个 Wi-Fi 后，在项目根目录运行：

```powershell
Set-Location E:\1a
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start_local_test.ps1
```

脚本会检查并启动项目目录中的 PostgreSQL，执行 `alembic upgrade head`，然后启动：

- FastAPI：`0.0.0.0:8000`
- Vite：`0.0.0.0:5173`

浏览器使用相对 API 地址 `/api/v1`，由 Vite 代理到电脑本机的
`http://127.0.0.1:8000`，因此手机端不需要配置 `localhost` 或固定 API IP。

查看电脑局域网地址：

```powershell
ipconfig
```

找到当前正在使用、且带有“默认网关”的 Wi-Fi/WLAN 网卡，读取其中的 IPv4 地址。
手机访问格式为：

```text
http://<电脑局域网IPv4>:5173
```

首次运行若出现 Windows 防火墙提示，应允许 Python 和 Node.js 访问“专用网络”。
服务日志和 PID 文件保存在 `.tmp/local-test/`。

## Phase 9.1：统一训练抽象

新增 `training_sessions` 和 `training_session_items`，作为专项、错题强化和混合训练的
统一底层。现有 `daily_tasks` 继续独立运行，本阶段没有修改每日 6 题推荐逻辑或移动端
入口。

通用训练支持：

- 按用户查询训练会话和历史
- 从任务项提交答案
- 恢复学生答案、标准解析和 AI 分析状态
- 后端校验全部题目完成后才能结束训练
- 复用现有规则判题、错题 AI 分析和 `knowledge_status` 更新
- 用户隔离与幂等答题

当前开放的基础接口：

```text
GET  /api/v1/training-sessions
GET  /api/v1/training-sessions/{session_id}
GET  /api/v1/training-sessions/{session_id}/answers
POST /api/v1/training-sessions/{session_id}/complete
POST /api/v1/training-session-items/{item_id}/answer
```

Phase 9.1 不提供学生创建训练的公开入口。训练会话由后端生成器通过统一服务创建；
Phase 9.2 将接入第一种生成器——学科专项训练。

## Phase 9.2：学科专项训练

移动端首页提供“学科专项训练”入口，不改变默认的今日 6 题流程。学生可以选择学科、章节、知识点和题量。后端优先选择最近 7 天未作答的题，并根据掌握度、近期错误和题目难度排序。题量不足时返回明确提示；判题、答案恢复、AI 错题分析和掌握度更新继续复用已有服务。

```text
GET  /api/v1/training-sessions/subject/catalog
POST /api/v1/training-sessions/subject
```

题库候选来源及引入限制见 `docs/QUESTION_BANK_SOURCES.md`。外部题库不得绕过现有 JSON 校验、去重和人工抽查流程直接写入数据库。

## Phase 11.3：每日任务刷新

尚未开始答题时，学生可以在首页更换一次当天的 6 道题：

- `POST /api/v1/daily-tasks/today/refresh`
- 每天最多成功刷新一次，任务版本由 `1` 更新为 `2`
- 刷新后的题目不会与刷新前的 6 道题重复
- 一旦已有答题记录或任务已完成，后端拒绝刷新
- 刷新通过数据库行锁串行处理，并发请求最多一个成功

升级数据库：

```powershell
E:\1a\.venv\Scripts\alembic.exe upgrade head
```

回滚到 Phase 11.2：

```powershell
E:\1a\.venv\Scripts\alembic.exe downgrade 20260723_0010
```

## Phase 11.4：学习报告

移动端“记录”页面展示今日、本周和近 7 天学习数据，并根据现有
`knowledge_status` 给出薄弱知识点 TOP3 与规则化训练建议：

```text
GET /api/v1/learning-report
```

- 今日和本周统计统一使用北京时间
- 本周从周一开始计算
- 最近趋势固定返回 7 个自然日，空数据日期也会返回
- 推荐方向由掌握度规则生成，不调用 LLM
- 本阶段只读聚合现有数据，不涉及数据库迁移
