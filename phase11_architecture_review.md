# Phase11 学习闭环架构评审

评审日期：2026-07-25  
评审范围：当前 FastAPI、Async SQLAlchemy、PostgreSQL、Vue3 移动端实现  
本报告性质：Step1 架构分析，不包含业务代码或数据库修改

## 1. 结论摘要

当前项目已经具备 Phase11 所需的大部分底层能力：

- `student_answers` 已保存用户、题目、提交答案、判题结果、AI分析状态、结构化AI结果、主观难度反馈和训练上下文。
- `questions` 与 `question_knowledge_points` 已覆盖110题，并且110题均有唯一有效的 primary 标准知识点。
- `training_sessions` 已支持 `subject`、`wrong_review` 等训练类型，专项训练提交会复用统一判题、AI分析和知识掌握度更新链路。
- 移动端已经有专项训练入口、目录选择页、训练答题页和刷新后答题状态恢复。
- 每日任务已具备“同一用户同一天唯一”、并发创建幂等、最近7天排除和完成状态服务端校验。

因此，Phase11不应重建训练系统或复制答题数据。推荐策略如下：

1. Phase11.1错题本直接聚合 `student_answers`，不新增表、不迁移数据库。
2. Phase11.2增强已有专项训练，切换到标准知识点关联查询并补充难度筛选，不新建训练表。
3. Phase11.3需要为 `daily_tasks` 增加刷新状态字段，必须单独创建Alembic迁移。
4. Phase11.4直接聚合 `student_answers` 和 `knowledge_status`，不新增报表快照表。

Phase11.1可以立即开发，风险最低。

## 2. 实际项目结构

### 2.1 后端

当前后端遵循分层结构：

- `app/models`：用户、题目、答题、每日任务、训练会话、知识状态、知识目录、导入日志。
- `app/schemas`：API请求与响应模型。
- `app/routers`：用户、题目、答题、每日任务、知识状态、通用训练接口。
- `app/services`：判题、AI分析、每日推荐、专项训练、训练会话、题库质量与发布。
- `app/api/router.py`：汇总全部业务路由。
- `app/main.py`：以配置中的API前缀挂载业务路由；当前默认对外形式为 `/api/...`。
- `alembic/versions`：当前迁移链到 `20260723_0010`。
- `tests`：覆盖AI降级、答题反馈、每日任务幂等与恢复、专项训练、知识点结构和题库发布。

### 2.2 前端

当前移动端结构：

- `views/HomeView.vue`：今日6题、任务恢复、加载及错误状态、专项训练入口。
- `views/QuestionView.vue`：每日任务答题、结果、标准解析、AI分析、主观反馈。
- `views/SubjectTrainingView.vue`：学科、章节、知识点和题量选择。
- `views/TrainingSessionView.vue`：通用训练作答、恢复、AI解析和完成。
- `views/StatsView.vue`：累计正确率、近期学习天数、最近20次答题。
- `services/api.ts`：统一API请求与鉴权。
- `stores/study.ts`：今日任务、答题结果和AI分析状态。
- `components/AppNav.vue`：目前只有“今日”和“记录”两个底部入口。

现有UI已经遵循移动端大按钮、单列卡片、底部安全区和错误降级风格。Phase11新增页面应复用这些模式。

## 3. 真实数据库基线

在本地真实PostgreSQL验证库中读取到：

| 项目 | 当前值 |
|---|---:|
| Alembic版本 | `20260723_0010` |
| users | 2 |
| questions | 110 |
| question_knowledge_points | 110 |
| student_answers | 25 |
| daily_tasks | 5 |
| daily_task_items | 30 |
| training_sessions | 2 |
| training_session_items | 7 |
| knowledge_status | 24 |

题库发布后已确认：

- 110题均有primary标准知识点。
- 当前没有孤立题目。
- 原60题数据未变化。

## 4. 当前学习数据关系

```text
users
 ├─ daily_tasks
 │   └─ daily_task_items ── questions
 │           └─ student_answers
 │
 ├─ training_sessions
 │   └─ training_session_items ── questions
 │           └─ student_answers
 │
 ├─ student_answers ── questions
 │       └─ ai_analysis（JSONB，保存在答题记录）
 │
 └─ knowledge_status ── knowledge_points

questions
 └─ question_knowledge_points ── knowledge_points
```

### 4.1 student_answers

`student_answers` 已满足错题本的事实数据需求：

- `user_id`：用户隔离。
- `question_id`：聚合同一道题的多次错误。
- `submitted_answer`：用户错误答案。
- `is_correct`：筛选错误记录。
- `analysis_status`、`ai_analysis`：AI分析状态与结构化结果。
- `created_at`：最近错误时间和日报、周报时间窗口。
- `difficulty_feedback`：学生主观反馈。
- `daily_task_item_id`、`training_session_item_id`：来源上下文。

现有索引包含：

- `question_id`
- `is_correct`
- `(user_id, created_at)`

当前单用户MVP和110题规模下，错题聚合不需要新增索引。后续用户量增大后，再根据实际慢查询考虑 `(user_id, is_correct, question_id, created_at)`，本阶段不提前迁移。

### 4.2 AI分析

错误答案创建后：

1. 后端规则判题。
2. 错题写入 `student_answers`，状态为 `pending`。
3. 后台任务调用集中式AI服务。
4. 成功后结构化结果保存到同一条答题记录的 `ai_analysis`。
5. AI识别的知识漏洞反向增加 `knowledge_status.ai_gap_count`。
6. AI失败时记录 `failed`，不影响答题结果和标准解析。

错题本应直接读取上述字段，不应再次调用LLM，也不应复制AI分析到新表。

### 4.3 knowledge_status

`knowledge_status` 同时保留：

- 旧字符串：`subject`、`knowledge_point`
- 标准ID：`knowledge_point_id`
- 映射信息：`mapping_version`、`mapped_at`
- 统计字段：尝试数、正确数、AI漏洞数、掌握度

Phase11查询应优先使用 `knowledge_point_id` 和标准知识目录，旧字符串只作为兼容回退。

当前答题更新逻辑仍以 `questions.knowledge_points[0]` 字符串定位知识状态。Phase11不能顺手重写这段核心逻辑；标准化更新应作为独立风险任务评估，避免破坏已验证的掌握度闭环。

## 5. Phase11.1 错题本设计评审

### 5.1 是否需要数据库迁移

不需要。

原因：

- 错误事实、错误次数、最近错误时间均可从 `student_answers` 聚合。
- 题目、答案和解析在 `questions`。
- AI分析在最近错误答题记录中。
- 标准知识点可通过 `question_knowledge_points` 和 `knowledge_points` 查询。
- 当前需求没有“收藏、忽略、人工移除、已攻克”这类需要持久状态的操作。

如果未来增加用户手动隐藏或标记已掌握，再评估单独的错题状态表；本阶段不能为了列表展示创建冗余表。

### 5.2 聚合口径

建议每个用户每道错题返回一条记录：

- 查询范围：`student_answers.user_id = 当前用户 AND is_correct = false`
- 分组：`question_id`
- `error_count`：该用户在该题上的错误记录数
- `last_wrong_at`：最大 `created_at`
- `latest_wrong_answer`：最近一次错误记录
- `submitted_answer`、`analysis_status`、`ai_analysis`：来自最近一次错误记录
- 题目内容、正确答案、解析、学科、章节和难度：来自 `questions`
- 标准知识点：来自该题唯一 `primary` 关联

本阶段“历史错题”定义为曾经答错过的题。后续答对不会自动删除历史错误，否则学生无法回顾真实错误轨迹。是否增加“已掌握”状态属于后续产品决策。

### 5.3 API建议

新增独立路由：

`GET /api/wrong-questions`

查询参数：

- `subject`：可选，精确匹配学科。
- `knowledge_point_code`：可选，使用稳定标准code。
- `sort`：默认 `error_count_desc`，第一版仅开放该值或内部固定。
- `page`：默认1。
- `page_size`：默认20，最大100。

建议响应：

- `items`
- `total`
- `page`
- `page_size`

每项包含：

- `question_id`
- `title`
- `content`
- `question_type`
- `options`
- `subject`
- `chapter`
- `knowledge_point_code`
- `knowledge_point_name`
- `difficulty`
- `submitted_answer`
- `correct_answer`
- `explanation`
- `analysis_status`
- `ai_analysis`
- `last_wrong_at`
- `error_count`

排序建议：

1. `error_count DESC`
2. `last_wrong_at DESC`
3. `question_id ASC`

必须使用当前登录用户ID过滤，不能接受前端传 `user_id`。

### 5.4 后端预计文件

新增：

- `app/routers/wrong_questions.py`
- `app/services/wrong_questions.py`
- `app/schemas/wrong_question.py`
- `tests/test_wrong_questions.py`

修改：

- `app/api/router.py`：注册路由。
- `app/schemas/__init__.py`、`app/routers/__init__.py`：如当前包导出方式需要。
- `README.md`：增加接口与测试说明。

不修改：

- `student_answers`表
- 判题逻辑
- AI分析服务
- 每日任务生成器
- 题库导入和发布

### 5.5 前端预计文件

新增：

- `frontend/src/views/WrongQuestionsView.vue`
- 可选的轻量展示组件，如 `WrongQuestionCard.vue`

修改：

- `frontend/src/router.ts`
- `frontend/src/services/api.ts`
- `frontend/src/types.ts`
- `frontend/src/components/AppNav.vue`

交互建议：

- 列表首屏按错误次数展示卡片。
- 卡片突出“学科、知识点、错误N次、最近错误时间”。
- 点击后在同页展开详情或进入轻量详情路由。
- 详情展示原题、我的答案、正确答案、标准解析和AI分析。
- AI状态为 `pending` 显示“分析中”；`failed` 或空值时只展示标准解析，不报致命错误。
- 空状态明确说明“完成训练后，答错的题会出现在这里”。

底部导航仍控制在三个入口以内：今日、错题、记录。专项训练继续从首页卡片进入，避免首页和导航同时堆叠过多按钮。

### 5.6 再次练习

数据库模型已经预留：

- `TrainingType.wrong_review`
- `TrainingSessionItem.source_answer_id`

因此再次练习应复用 `training_sessions`，不新建错题训练表。Phase11.1最小上线可以先完成错题浏览；若同阶段加入“再练一次”，建议增加窄接口创建 `wrong_review` 会话，并通过现有训练答题页完成提交、AI分析和掌握度更新。

不能让前端直接提交任意题目ID绕过用户错题归属校验。

## 6. Phase11.2 专项训练设计评审

### 6.1 当前完成度

专项训练已经存在：

- `GET /api/training-sessions/subject/catalog`
- `POST /api/training-sessions/subject`
- `SubjectTrainingView.vue`
- `TrainingSessionView.vue`
- 指定学科、章节、知识点和题量
- 训练记录进入 `student_answers`
- 错题触发AI分析
- 统一更新 `knowledge_status`
- 训练完成由服务端校验

所以Phase11.2应定义为“增强和标准化”，不能另建一套专项训练。

### 6.2 当前缺口

1. 目录和筛选仍读取旧 `questions.knowledge_points` 字符串，没有使用标准 `question_knowledge_points`。
2. 请求使用知识点名称，名称变更会影响稳定性，应改用或新增 `knowledge_point_code`。
3. 当前没有用户指定难度的字段。
4. 当前“最近7天”只是排序靠后，不是严格排除；需要产品上明确。
5. `training_sessions.knowledge_point` 仍为字符串，可继续兼容；稳定code可保存在 `selection_config`，避免本阶段迁移表结构。

### 6.3 推荐实现

- 目录查询从 `knowledge_points → question_knowledge_points → questions` 构建。
- 前端展示标准名称，提交稳定 `knowledge_point_code`。
- `SubjectTrainingCreate` 增加可选难度：
  - 最简方案：`difficulty: int | None`
  - 若要范围：`difficulty_min`、`difficulty_max`
- 指定难度时先过滤，再进行掌握度和近期错误排序。
- 训练创建、答题和完成继续复用现有 `training_sessions` 服务。
- `selection_config`记录知识点code、难度条件和算法版本。

### 6.4 数据库变化

第一版不需要迁移。

已有表足够表达专项训练。若未来必须高频按标准知识点统计训练会话，再考虑给 `training_sessions` 增加 `knowledge_point_id`；当前单学生MVP无需提前增加。

## 7. Phase11.3 每日任务刷新设计评审

### 7.1 当前约束

- `daily_tasks`对 `(user_id, task_date)` 有唯一约束。
- 每日任务项对 `(daily_task_id, position)` 和 `(daily_task_id, question_id)` 有唯一约束。
- `get_or_create_today`并发冲突时读取已创建任务，当前创建幂等稳定。
- 生成器排除用户最近7天做过的题。
- `student_answers.daily_task_item_id`删除时会 `SET NULL`，但丢失任务项关联仍会削弱历史追溯。

### 7.2 必需迁移

Phase11.3需要Alembic迁移，建议新增：

- `daily_tasks.refresh_count INTEGER NOT NULL DEFAULT 0`
- `daily_tasks.version INTEGER NOT NULL DEFAULT 1`

迁移原因：

- `refresh_count`是每天最多刷新一次的服务端约束依据。
- `version`让前端和日志明确当前任务是初始版本还是刷新版本。
- 现有 `recommendation_version`表示算法版本 `rules-v1`，不能混用为任务版本。

回滚：

- `downgrade`删除 `version` 和 `refresh_count`。
- 两列不承载已有业务外键，回滚不会修改任务、任务项或答题记录。
- 正式迁移前备份数据库，升级后验证旧任务均为 `refresh_count=0, version=1`。

### 7.3 刷新规则

建议接口：

`POST /api/daily-tasks/today/refresh`

事务内流程：

1. 使用北京时间确定今日。
2. 对今日 `daily_tasks` 行 `SELECT ... FOR UPDATE`。
3. 若任务不存在，先按现有逻辑生成版本1；是否同时刷新需明确，建议返回版本1而不消耗刷新次数。
4. 若 `refresh_count >= 1`，返回409。
5. 若任务已完成，返回409。
6. 若当前六个任务项已有任何答题记录，返回409，避免破坏历史答题上下文。
7. 新推荐必须排除：
   - 最近7天做过的题；
   - 当前版本的6道题；
   - 同一新版本内部重复题。
8. 在同一事务内替换未答任务项：
   - `refresh_count=1`
   - `version=2`
   - 保持同一个 `daily_task.id`
9. 返回版本2任务。

并发请求依靠行锁串行化。第一个请求成功后，第二个请求看到 `refresh_count=1` 并返回409，不会生成第三套题。

不建议刷新已经开始作答的任务。虽然删除任务项后外键可置空，但会使历史答题失去每日任务上下文，不符合“不影响历史答题记录”。

## 8. Phase11.4 学习报告设计评审

### 8.1 数据来源

不新增报表表，实时聚合：

- 今日与本周完成题数、正确数：`student_answers`
- 薄弱知识点：`knowledge_status`
- 推荐训练方向：规则生成，不调用LLM

### 8.2 时间口径

统一使用北京时间：

- 今日：北京时间00:00至次日00:00，转换为UTC后查询带时区时间戳。
- 本周：北京时间周一00:00至下周一00:00。
- 前端不自行拼接统计窗口，后端返回已计算数据。

### 8.3 API建议

`GET /api/learning-reports/summary`

返回：

- `today.completed_count`
- `today.correct_count`
- `today.accuracy`
- `week.completed_count`
- `week.correct_count`
- `week.average_accuracy`
- `weak_knowledge_points`：最多3项，带标准code、名称、学科、掌握度
- `recommended_directions`：规则生成的简短方向

薄弱知识点排序建议：

1. `mastery_score ASC`
2. `ai_gap_count DESC`
3. `attempt_count DESC`

为避免一次偶然错误压过稳定薄弱点，可优先纳入已有尝试记录的知识点。

### 8.4 前端

现有 `StatsView.vue` 只有累计统计和最近答题，应升级为学习报告页：

- 顶部今日卡片
- 本周概览
- 薄弱知识点TOP3
- 推荐专项入口
- 最近记录保留但下移

不要新建复杂图表系统。简单进度条、数字卡片和知识点列表足够。

## 9. 兼容性与主要风险

### 9.1 标准知识点与旧字符串并存

这是Phase11最大的技术债：

- 新题已全部建立标准primary关联。
- 推荐与掌握度更新仍大量依赖 `questions.knowledge_points` 字符串。
- `knowledge_status`虽已回填标准ID，但唯一约束仍基于旧字符串。

Phase11.1查询可以安全使用标准关联；Phase11.2也应优先标准关联。但不能在本阶段顺带删除旧字段或改变掌握度唯一约束。

### 9.2 错题列表的SQL正确性

取“最近一次错误答案”不能只 `GROUP BY` 后随意选择JSON字段。应使用PostgreSQL窗口函数、`DISTINCT ON`或先聚合再回连最近记录，确保答案、AI分析和时间来自同一条记录。

### 9.3 用户数据隔离

所有错题、训练和报告查询必须以JWT解析出的当前用户ID为条件。知识点筛选不能绕过用户条件。

### 9.4 AI异步状态

错题本可能在AI仍为 `pending` 时打开。页面必须支持 pending、completed、failed 和无分析四种状态，不能因AI失败让整个错题详情失败。

### 9.5 每日刷新历史

刷新已答任务会破坏任务项级别的恢复与完成校验。第一版必须限制为“尚未作答时可刷新一次”。

### 9.6 首页复杂度

首页仍以今日训练为主。推荐入口分配：

- 首页主卡：今日6题
- 首页次卡：专项训练
- 底部导航：今日、错题、记录

不增加更多并列入口。

## 10. 分阶段实施顺序

### Step2：Phase11.1错题本

后端先行：

1. 错题聚合schema、service、router。
2. 学科与标准知识点筛选。
3. 分页、错误次数排序和AI降级。
4. 接口测试。

前端随后：

1. 类型和API方法。
2. 错题列表与详情。
3. 导航入口、加载、空状态和错误状态。
4. TypeScript检查与生产构建。

数据库：

- 无迁移。
- 在真实PostgreSQL上核对返回结果与当前25条答题记录一致。

### Step3：Phase11.2专项训练增强

1. 目录改用标准知识点关联。
2. API支持标准code和难度。
3. 复用现有训练会话与答题页面。
4. 回归判题、AI分析和掌握度更新。

数据库：

- 预计无迁移。

### Step4：Phase11.3每日任务刷新

1. 单独Alembic迁移。
2. 服务端刷新事务和并发控制。
3. 前端刷新按钮及剩余次数提示。
4. 验证未作答可刷新、已作答/已完成/第二次刷新被拒绝。

### Step5：Phase11.4学习报告

1. 北京时间统计服务。
2. 今日、周、薄弱TOP3和规则建议接口。
3. 升级记录页。
4. 与当前累计统计做兼容。

## 11. Step2建议验收标准

Phase11.1完成后至少验证：

- 只返回当前用户曾答错的题。
- 同一题多次错误只返回一项，错误次数准确。
- 最近错误答案、时间和AI分析来自同一条记录。
- 学科筛选准确。
- 标准知识点code筛选准确。
- 默认按错误次数降序，次数相同按最近错误时间降序。
- 正确答案和标准解析来自后端，前端不能构造。
- AI pending/failed不影响列表和详情。
- 无错题时返回稳定空列表。
- 后端接口测试通过。
- 前端类型检查和生产构建通过。
- 数据库结构和现有110题不变化。

## 12. 是否建议进入Step2

建议。

Phase11.1不需要数据库迁移，可以完全复用当前数据模型，且不会触碰每日任务生成、AI调用、知识掌握度更新或题库发布流程。它是当前风险最低、对真实学生价值最直接的下一步。
