# Revision C Dry Run v2 报告

报告日期：2026-07-23  
映射版本：`kp-mapping-v1.1`  
数据库版本：`20260723_0008`  
数据来源：`knowledge_catalog_revision_plan.md`、`knowledge_point_mapping.md`、PostgreSQL 当前题目与知识点目录。  
执行方式：只读检查。未修改数据库，未创建迁移，未写入 `question_knowledge_points`，未执行 Revision C。

## 一、结论

| 检查项 | 结果 |
|---|---:|
| 当前题目数 | 60 |
| 题目 ID 范围 | 1—60 |
| 唯一题目 ID | 60 |
| 数学 / 物理 / 英语题目数 | 20 / 20 / 20 |
| 计划生成的 primary 关联 | 60 |
| 缺少 primary 的题目 | 0 |
| 存在多个 primary 的题目 | 0 |
| 最终使用的不同三级 code | 57 |
| 数据库中存在的目标 code | 57 |
| 缺失或未启用的目标 code | 0 |
| 跨学科关联 | 0 |
| 错误使用 redirected 节点 | 0 |
| 错误使用 ability_only 节点 | 0 |
| 错误使用 deprecated 节点 | 0 |
| high confidence | 59 |
| medium confidence | 1 |
| 当前 `question_knowledge_points` 行数 | 0 |

**Dry Run 结论：通过。**

Revision B.1 已补齐原先缺失的 6 个 v1.1 code。全部 57 个最终目标 code 均存在于 `knowledge_points`，且均为启用的三级知识点。当前已满足 Revision C 的数据前置条件，但本报告不授权也不执行正式迁移，需等待人工确认。

## 二、60 道题最终关联预览

### 数学

| question_id | old_knowledge_point | new_knowledge_point_code | standard_name | role | action | reason | confidence |
|---:|---|---|---|---|---|---|---|
| 1 | 集合的交集 | `MATH-SET-OPERATIONS` | 集合的基本运算 | primary | broaden | 交集属于集合基本运算，扩大后可覆盖并、交、补集 | high |
| 2 | 充分条件与必要条件 | `MATH-LOGIC-SUFFICIENT-NECESSARY` | 充分条件与必要条件 | primary | keep | 旧标签与题目考查内容一致 | high |
| 3 | 函数定义域 | `MATH-FUNCTION-DOMAIN` | 函数的定义域 | primary | rename | 统一教材常用名称 | high |
| 4 | 函数单调性 | `MATH-FUNCTION-MONOTONICITY` | 函数的单调性 | primary | rename | 统一教材常用名称 | high |
| 5 | 函数奇偶性 | `MATH-FUNCTION-PARITY` | 函数的奇偶性 | primary | rename | 统一教材常用名称 | high |
| 6 | 指数运算 | `MATH-EXPONENT-OPERATION` | 指数运算 | primary | keep | 题目直接考查同底数幂运算 | high |
| 7 | 对数运算 | `MATH-LOGARITHM-OPERATION` | 对数运算 | primary | keep | 题目直接考查对数定义与运算 | high |
| 8 | 特殊角三角函数值 | `MATH-TRIG-SPECIAL-ANGLE` | 特殊角的三角函数值 | primary | rename | 统一中文表达 | high |
| 9 | 同角三角函数关系 | `MATH-TRIG-FUNDAMENTAL-IDENTITY` | 同角三角函数的基本关系 | primary | rename | 使用教材标准表述 | high |
| 10 | 向量坐标运算 | `MATH-VECTOR-COORDINATE` | 平面向量的坐标运算 | primary | rename | 明确限定为平面向量 | high |
| 11 | 等差数列通项 | `MATH-SEQUENCE-ARITHMETIC-GENERAL` | 等差数列的通项公式 | primary | rename | 使用教材标准表述 | high |
| 12 | 等比数列通项 | `MATH-SEQUENCE-GEOMETRIC-GENERAL` | 等比数列的通项公式 | primary | rename | 使用教材标准表述 | high |
| 13 | 一元二次不等式 | `MATH-INEQUALITY-QUADRATIC` | 一元二次不等式的解法 | primary | rename | 明确训练目标为求解 | high |
| 14 | 空间线面关系 | `MATH-SOLID-LINE-PLANE-PERPENDICULAR` | 直线与平面垂直的判定 | primary | rename | 题目实际考查线面垂直判定定理 | high |
| 15 | 直线斜率 | `MATH-ANALYTIC-LINE-SLOPE` | 直线的斜率 | primary | rename | 统一中文表达 | high |
| 16 | 圆的标准方程 | `MATH-ANALYTIC-CIRCLE-STANDARD` | 圆的标准方程 | primary | keep | 旧标签与题目完全一致 | high |
| 17 | 古典概型 | `MATH-PROBABILITY-CLASSICAL` | 古典概型 | primary | keep | 题目考查等可能事件概率 | high |
| 18 | 平均数 | `MATH-STATISTICS-MEAN` | 平均数 | primary | keep | 题目直接考查算术平均数 | high |
| 19 | 基本初等函数的导数 | `MATH-DERIVATIVE-ELEMENTARY` | 基本初等函数的导数 | primary | keep | 题目直接考查幂函数求导 | high |
| 20 | 复数运算 | `MATH-COMPLEX-ARITHMETIC` | 复数的四则运算 | primary | rename | 明确运算知识点范围 | high |

### 物理

| question_id | old_knowledge_point | new_knowledge_point_code | standard_name | role | action | reason | confidence |
|---:|---|---|---|---|---|---|---|
| 21 | 质点 | `PHY-MOTION-PARTICLE-MODEL` | 质点模型 | primary | rename | 强调物理模型及适用条件 | high |
| 22 | 位移与路程 | `PHY-MOTION-DISPLACEMENT-DISTANCE` | 位移与路程 | primary | keep | 题目直接辨析位移与路程 | high |
| 23 | 速度公式 | `PHY-KINEMATICS-UNIFORM-ACCELERATION` | 匀变速直线运动规律 | primary | broaden | 速度公式属于匀变速直线运动规律，避免公式级碎片化 | high |
| 24 | 自由落体 | `PHY-KINEMATICS-FREE-FALL` | 自由落体运动 | primary | rename | 使用标准物理名称 | high |
| 25 | 力的合成 | `PHY-FORCE-COMPOSITION` | 力的合成 | primary | keep | 题目直接考查同向力合成 | high |
| 26 | 牛顿第三定律 | `PHY-NEWTON-THIRD-LAW` | 牛顿第三定律 | primary | keep | 题目考查作用力与反作用力 | high |
| 27 | 牛顿第二定律 | `PHY-NEWTON-SECOND-LAW` | 牛顿第二定律 | primary | keep | 题目直接应用 F=ma | high |
| 28 | 平抛运动 | `PHY-PROJECTILE-HORIZONTAL` | 平抛运动规律 | primary | rename | 题目考查平抛水平方向运动规律 | high |
| 29 | 向心加速度 | `PHY-CIRCULAR-CENTRIPETAL-ACCELERATION` | 向心加速度 | primary | keep | 题目直接考查向心加速度公式 | high |
| 30 | 万有引力定律 | `PHY-GRAVITY-UNIVERSAL-LAW` | 万有引力定律 | primary | keep | 题目考查万有引力比例关系 | high |
| 31 | 功 | `PHY-WORK-ENERGY-WORK-CALCULATION` | 功的概念与计算 | primary | rename | 统一粒度并覆盖功的含义与计算 | high |
| 32 | 动能 | `PHY-WORK-ENERGY-KINETIC` | 动能概念与计算 | primary | rename | 避免使用过宽的单词标签 | high |
| 33 | 动量 | `PHY-MOMENTUM-BASIC` | 动量概念与计算 | primary | rename | 避免与二级模块同名 | high |
| 34 | 库仑定律 | `PHY-ELECTROSTATICS-COULOMB-LAW` | 库仑定律 | primary | keep | 题目考查同种电荷相斥 | high |
| 35 | 欧姆定律 | `PHY-CIRCUIT-OHM-LAW` | 欧姆定律 | primary | keep | 题目直接应用 R=U/I | high |
| 36 | 电功率 | `PHY-CIRCUIT-ELECTRIC-POWER` | 电功率的计算 | primary | rename | 明确训练目标为电功率计算 | high |
| 37 | 磁场方向 | `PHY-MAGNETIC-FIELD-DIRECTION` | 磁场方向的判定 | primary | rename | 题目考查磁场方向定义与判定 | high |
| 38 | 感应电流条件 | `PHY-INDUCTION-CURRENT-CONDITION` | 感应电流的产生条件 | primary | rename | 使用标准物理表述 | high |
| 39 | 波速公式 | `PHY-WAVE-SPEED-FREQUENCY-WAVELENGTH` | 波速、波长与频率的关系 | primary | rename | 从公式名称提升为三个物理量关系 | high |
| 40 | 光的折射 | `PHY-OPTICS-REFRACTION` | 光的折射规律 | primary | broaden | 折射现象纳入可扩充的折射规律知识点 | high |

### 英语

| question_id | old_knowledge_point | new_knowledge_point_code | standard_name | role | action | reason | confidence |
|---:|---|---|---|---|---|---|---|
| 41 | 动词辨析 | `ENG-VOCAB-COLLOCATION` | 固定搭配 | primary | fix | 正确性来自 `pay attention to` 固定搭配 | high |
| 42 | 形容词辨析 | `ENG-VOCAB-CONTEXT-VERB` | 动词语境辨析 | primary | fix | 四个选项均为动词，原词性标签错误 | high |
| 43 | 一般现在时 | `ENG-GRAMMAR-TENSE-PRESENT-SIMPLE` | 一般现在时 | primary | keep | `every Sunday` 明确考查一般现在时 | high |
| 44 | 现在完成时 | `ENG-GRAMMAR-TENSE-PRESENT-PERFECT` | 现在完成时 | primary | keep | `twice` 和语境明确指向现在完成时 | high |
| 45 | 过去进行时 | `ENG-GRAMMAR-TENSE-PAST-CONTINUOUS` | 过去进行时 | primary | keep | 过去具体时刻正在发生的动作 | high |
| 46 | 一般现在时的被动语态 | `ENG-GRAMMAR-VOICE-PRESENT-PASSIVE` | 一般现在时的被动语态 | primary | rename | code 不变，仅统一中文名称 | high |
| 47 | 动词不定式 | `ENG-NONFINITE-INFINITIVE` | 动词不定式 | primary | keep | `decide to do` 明确考查不定式 | high |
| 48 | 动名词 | `ENG-NONFINITE-INFINITIVE` | 动词不定式 | primary | fix | `a way to do` 实际考查不定式，原标签错误 | high |
| 49 | 关系代词 that | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 定语从句关系词的选择 | primary | merge | 合并为关系词整体选择能力，that 保留为内容标签 | high |
| 50 | 关系副词 where | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 定语从句关系词的选择 | primary | merge | 与 that 题共同训练从句成分和关系词选择 | high |
| 51 | 宾语从句语序 | `ENG-CLAUSE-OBJECT-WORD-ORDER` | 宾语从句的语序 | primary | rename | 统一中文表达 | high |
| 52 | 条件状语从句 | `ENG-CLAUSE-ADVERBIAL-CONDITION` | 条件状语从句 | primary | keep | 题目考查条件从句“主将从现” | high |
| 53 | 情态动词 must | `ENG-GRAMMAR-MODAL-BASIC` | 情态动词的基本用法 | primary | broaden | must 纳入情态动词基本语义和语境判断 | high |
| 54 | 就近原则 | `ENG-GRAMMAR-AGREEMENT-PROXIMITY` | 主谓一致的就近原则 | primary | rename | 补充所属语法范围 | high |
| 55 | 比较级 | `ENG-GRAMMAR-ADJECTIVE-COMPARATIVE` | 形容词比较级 | primary | rename | 明确考查词类 | high |
| 56 | 介词搭配 | `ENG-VOCAB-COLLOCATION` | 固定搭配 | primary | merge | `be interested in` 归入固定搭配，与 ID 41 复用画像节点 | high |
| 57 | 事实细节 | `ENG-READING-DETAIL` | 细节理解 | primary | rename | 使用高考阅读常用名称 | high |
| 58 | 主旨大意 | `ENG-READING-MAIN-IDEA` | 主旨大意 | primary | keep | 题目直接判断文章主旨 | high |
| 59 | there be 句型 | `ENG-GRAMMAR-THERE-BE` | There be句型 | primary | rename | code 不变，统一显示格式 | high |
| 60 | 句子翻译 | `ENG-NONFINITE-GERUND-SUBJECT` | 动名词短语作主语 | primary | reclassify | 句子翻译降为能力标签；参考答案使用动名词短语作主语 | medium |

## 三、校验明细

### 1. 题目与 primary 完整性

- PostgreSQL 中存在 60 道题，ID 为 1—60，且 60 个 ID 均唯一。
- 数学、物理、英语各 20 道。
- 固定映射包含 60 行、60 个唯一 `question_id`。
- 每题恰好一个 `primary`；没有缺失或重复 primary。
- 本次不推断、不预览 secondary 关联。

### 2. 目标 code 存在性

- 60 条映射最终使用 57 个不同 code。
- 57 个 code 在 `knowledge_points` 中全部存在。
- 57 个目标节点全部满足 `level=3` 且 `is_active=true`。
- Revision B.1 新增的 6 个 code 均已存在：

| code | standard_name | 影响题目 |
|---|---|---|
| `MATH-SET-OPERATIONS` | 集合的基本运算 | 1 |
| `PHY-KINEMATICS-UNIFORM-ACCELERATION` | 匀变速直线运动规律 | 23 |
| `PHY-OPTICS-REFRACTION` | 光的折射规律 | 40 |
| `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 定语从句关系词的选择 | 49、50 |
| `ENG-GRAMMAR-MODAL-BASIC` | 情态动词的基本用法 | 53 |
| `ENG-NONFINITE-GERUND-SUBJECT` | 动名词短语作主语 | 60 |

### 3. 跨学科检查

| 题目学科 | 题目数 | 目标 code 前缀 | 不匹配 |
|---|---:|---|---:|
| 数学 | 20 | `MATH-` | 0 |
| 物理 | 20 | `PHY-` | 0 |
| 英语 | 20 | `ENG-` | 0 |

不存在跨学科关联。

### 4. redirected / ability_only / deprecated 检查

以下 v1 旧节点不得作为 Revision C 的最终目标：

| 旧 code | v1.1 状态 | 最终处理 |
|---|---|---|
| `MATH-SET-INTERSECTION` | redirected | 使用 `MATH-SET-OPERATIONS` |
| `PHY-KINEMATICS-VELOCITY-EQUATION` | redirected | 使用 `PHY-KINEMATICS-UNIFORM-ACCELERATION` |
| `PHY-OPTICS-REFRACTION-PHENOMENON` | redirected | 使用 `PHY-OPTICS-REFRACTION` |
| `ENG-CLAUSE-RELATIVE-THAT` | redirected | 使用 `ENG-CLAUSE-RELATIVE-WORD-SELECTION` |
| `ENG-CLAUSE-RELATIVE-WHERE` | redirected | 使用 `ENG-CLAUSE-RELATIVE-WORD-SELECTION` |
| `ENG-GRAMMAR-MODAL-MUST` | redirected | 使用 `ENG-GRAMMAR-MODAL-BASIC` |
| `ENG-WRITING-SENTENCE-EXPRESSION` | ability_only | 使用 `ENG-NONFINITE-GERUND-SUBJECT`；`sentence_expression` 仅保留为能力标签 |

最终 60 条映射没有使用上述旧节点，也没有使用任何 deprecated 节点。

### 5. 人工确认提示

没有数据库层面的阻断项。

题目 ID 60 仍是唯一的 `medium confidence` 映射：以当前标准答案体现的“动名词短语作主语”作为 primary；“句子翻译”和 `sentence_expression` 只作为题型/能力语义，不写入 `question_knowledge_points`。该处理已纳入已确认的 `kp-mapping-v1.1`，正式 Revision C 前建议在审批记录中再次明确保留此决定。

## 四、只读边界验证

- Dry Run 前后 `question_knowledge_points` 均为 0 行。
- 未修改 `questions`。
- 未修改 `knowledge_points`。
- 未修改 `knowledge_status`。
- 未创建 Alembic migration。
- 未执行 Revision C。

## 五、Revision C 执行门槛

当前检查状态：

```text
Revision C readiness: PASS
Database blockers: 0
Manual execution authorization: PENDING
```

只有在人工明确确认本报告后，才可另行执行 Revision C 正式迁移。
