# 现有60题知识点标准映射设计

设计日期：2026-07-23  
依据文件：`knowledge_point_review.md`  
适用范围：当前数学、物理、英语共60道题的第二阶段知识点设计。  
执行边界：本文件仅定义映射，不修改数据库、代码、题目内容或现有JSON。

## 一、知识点编码规范

### 1. 编码结构

```text
<SUBJECT>-<MODULE>-<TOPIC>[-<SUBTOPIC>]
```

- `SUBJECT`：固定学科前缀。
  - `MATH`：数学
  - `PHY`：物理
  - `ENG`：英语
- `MODULE`：稳定的二级模块，如 `FUNCTION`、`KINEMATICS`、`READING`。
- `TOPIC`：可反复关联多道题的三级知识点。
- `SUBTOPIC`：仅在不增加该段就会产生歧义时使用。
- 全部使用大写英文字母和连字符，不使用空格、中文、题目ID、年份、教材页码。

### 2. 稳定性规则

1. 编码表达知识概念，不表达某一道具体题。
2. 编码一旦进入正式使用，不因中文显示名称调整而修改。
3. 相同知识点的不同题型、难度和来源复用同一编码。
4. “选择题”“翻译题”“计算题”等属于题型或能力标签，不写入知识点编码。
5. 同义名称通过映射或别名合并，不创建多个近义编码。
6. 一个编码只属于一个学科；跨学科同名概念也应使用不同学科前缀。
7. 当前编码代表三级知识点，不能直接使用只有学科或模块的过宽编码。

### 3. action定义

| action | 含义 |
|---|---|
| `keep` | 旧名称已经适合作为标准名称 |
| `rename` | 知识点正确，仅规范名称或细化粒度 |
| `merge` | 与其他旧名称统一到同一个标准知识点 |
| `fix` | 原标签与题目实际考查内容不一致，需要纠正 |

### 4. confidence定义

| confidence | 含义 |
|---|---|
| `high` | 题干、答案和解析均明确支持该映射 |
| `medium` | 映射合理，但存在知识点与能力标签边界，需要人工定稿 |
| `low` | 仅靠当前题目信息无法可靠判断，迁移前必须补充审核 |

## 二、60道题完整映射

### 数学

| question_id | old knowledge_point | standard knowledge_point_id | standard_name | chapter | action | confidence |
|---:|---|---|---|---|---|---|
| 1 | 集合的交集 | `MATH-SET-INTERSECTION` | 集合的基本运算（交集） | 集合与常用逻辑用语 | rename | high |
| 2 | 充分条件与必要条件 | `MATH-LOGIC-SUFFICIENT-NECESSARY` | 充分条件与必要条件 | 集合与常用逻辑用语 | keep | high |
| 3 | 函数定义域 | `MATH-FUNCTION-DOMAIN` | 函数的定义域 | 函数 | rename | high |
| 4 | 函数单调性 | `MATH-FUNCTION-MONOTONICITY` | 函数的单调性 | 函数 | rename | high |
| 5 | 函数奇偶性 | `MATH-FUNCTION-PARITY` | 函数的奇偶性 | 函数 | rename | high |
| 6 | 指数运算 | `MATH-EXPONENT-OPERATION` | 指数运算 | 指数函数与对数函数 | keep | high |
| 7 | 对数运算 | `MATH-LOGARITHM-OPERATION` | 对数运算 | 指数函数与对数函数 | keep | high |
| 8 | 特殊角三角函数值 | `MATH-TRIG-SPECIAL-ANGLE` | 特殊角的三角函数值 | 三角函数 | rename | high |
| 9 | 同角三角函数关系 | `MATH-TRIG-FUNDAMENTAL-IDENTITY` | 同角三角函数的基本关系 | 三角函数 | rename | high |
| 10 | 向量坐标运算 | `MATH-VECTOR-COORDINATE` | 平面向量的坐标运算 | 平面向量 | rename | high |
| 11 | 等差数列通项 | `MATH-SEQUENCE-ARITHMETIC-GENERAL` | 等差数列的通项公式 | 数列 | rename | high |
| 12 | 等比数列通项 | `MATH-SEQUENCE-GEOMETRIC-GENERAL` | 等比数列的通项公式 | 数列 | rename | high |
| 13 | 一元二次不等式 | `MATH-INEQUALITY-QUADRATIC` | 一元二次不等式的解法 | 不等式 | rename | high |
| 14 | 空间线面关系 | `MATH-SOLID-LINE-PLANE-PERPENDICULAR` | 直线与平面垂直的判定 | 立体几何 | rename | high |
| 15 | 直线斜率 | `MATH-ANALYTIC-LINE-SLOPE` | 直线的斜率 | 解析几何 | rename | high |
| 16 | 圆的标准方程 | `MATH-ANALYTIC-CIRCLE-STANDARD` | 圆的标准方程 | 解析几何 | keep | high |
| 17 | 古典概型 | `MATH-PROBABILITY-CLASSICAL` | 古典概型 | 概率 | keep | high |
| 18 | 平均数 | `MATH-STATISTICS-MEAN` | 平均数 | 统计 | keep | high |
| 19 | 基本初等函数的导数 | `MATH-DERIVATIVE-ELEMENTARY` | 基本初等函数的导数 | 导数 | keep | high |
| 20 | 复数运算 | `MATH-COMPLEX-ARITHMETIC` | 复数的四则运算 | 复数 | rename | high |

### 物理

| question_id | old knowledge_point | standard knowledge_point_id | standard_name | chapter | action | confidence |
|---:|---|---|---|---|---|---|
| 21 | 质点 | `PHY-MOTION-PARTICLE-MODEL` | 质点模型 | 运动的描述 | rename | high |
| 22 | 位移与路程 | `PHY-MOTION-DISPLACEMENT-DISTANCE` | 位移与路程 | 运动的描述 | keep | high |
| 23 | 速度公式 | `PHY-KINEMATICS-VELOCITY-EQUATION` | 匀变速直线运动速度公式 | 匀变速直线运动 | rename | high |
| 24 | 自由落体 | `PHY-KINEMATICS-FREE-FALL` | 自由落体运动 | 匀变速直线运动 | rename | high |
| 25 | 力的合成 | `PHY-FORCE-COMPOSITION` | 力的合成 | 相互作用 | keep | high |
| 26 | 牛顿第三定律 | `PHY-NEWTON-THIRD-LAW` | 牛顿第三定律 | 相互作用 | keep | high |
| 27 | 牛顿第二定律 | `PHY-NEWTON-SECOND-LAW` | 牛顿第二定律 | 牛顿运动定律 | keep | high |
| 28 | 平抛运动 | `PHY-PROJECTILE-HORIZONTAL` | 平抛运动规律 | 曲线运动 | rename | high |
| 29 | 向心加速度 | `PHY-CIRCULAR-CENTRIPETAL-ACCELERATION` | 向心加速度 | 圆周运动 | keep | high |
| 30 | 万有引力定律 | `PHY-GRAVITY-UNIVERSAL-LAW` | 万有引力定律 | 万有引力 | keep | high |
| 31 | 功 | `PHY-WORK-ENERGY-WORK-CALCULATION` | 功的计算 | 机械能 | rename | high |
| 32 | 动能 | `PHY-WORK-ENERGY-KINETIC` | 动能概念与计算 | 机械能 | rename | high |
| 33 | 动量 | `PHY-MOMENTUM-BASIC` | 动量概念与计算 | 动量 | rename | high |
| 34 | 库仑定律 | `PHY-ELECTROSTATICS-COULOMB-LAW` | 库仑定律 | 静电场 | keep | high |
| 35 | 欧姆定律 | `PHY-CIRCUIT-OHM-LAW` | 欧姆定律 | 恒定电流 | keep | high |
| 36 | 电功率 | `PHY-CIRCUIT-ELECTRIC-POWER` | 电功率的计算 | 恒定电流 | rename | high |
| 37 | 磁场方向 | `PHY-MAGNETIC-FIELD-DIRECTION` | 磁场方向的判定 | 磁场 | rename | high |
| 38 | 感应电流条件 | `PHY-INDUCTION-CURRENT-CONDITION` | 感应电流的产生条件 | 电磁感应 | rename | high |
| 39 | 波速公式 | `PHY-WAVE-SPEED-FREQUENCY-WAVELENGTH` | 波速、波长与频率的关系 | 机械振动与机械波 | rename | high |
| 40 | 光的折射 | `PHY-OPTICS-REFRACTION-PHENOMENON` | 光的折射现象 | 光学 | rename | high |

### 英语

| question_id | old knowledge_point | standard knowledge_point_id | standard_name | chapter | action | confidence |
|---:|---|---|---|---|---|---|
| 41 | 动词辨析 | `ENG-VOCAB-COLLOCATION` | 固定搭配 | 词汇 | merge | high |
| 42 | 形容词辨析 | `ENG-VOCAB-CONTEXT-VERB` | 动词语境辨析 | 词汇 | fix | high |
| 43 | 一般现在时 | `ENG-GRAMMAR-TENSE-PRESENT-SIMPLE` | 一般现在时 | 时态 | keep | high |
| 44 | 现在完成时 | `ENG-GRAMMAR-TENSE-PRESENT-PERFECT` | 现在完成时 | 时态 | keep | high |
| 45 | 过去进行时 | `ENG-GRAMMAR-TENSE-PAST-CONTINUOUS` | 过去进行时 | 时态 | keep | high |
| 46 | 一般现在时的被动语态 | `ENG-GRAMMAR-VOICE-PRESENT-PASSIVE` | 一般现在时被动语态 | 语态 | rename | high |
| 47 | 动词不定式 | `ENG-NONFINITE-INFINITIVE` | 动词不定式 | 非谓语动词 | keep | high |
| 48 | 动名词 | `ENG-NONFINITE-INFINITIVE` | 动词不定式 | 非谓语动词 | fix | high |
| 49 | 关系代词 that | `ENG-CLAUSE-RELATIVE-THAT` | 关系代词 that 的用法 | 定语从句 | rename | high |
| 50 | 关系副词 where | `ENG-CLAUSE-RELATIVE-WHERE` | 关系副词 where 的用法 | 定语从句 | rename | high |
| 51 | 宾语从句语序 | `ENG-CLAUSE-OBJECT-WORD-ORDER` | 宾语从句的语序 | 名词性从句 | rename | high |
| 52 | 条件状语从句 | `ENG-CLAUSE-ADVERBIAL-CONDITION` | 条件状语从句 | 状语从句 | keep | high |
| 53 | 情态动词 must | `ENG-GRAMMAR-MODAL-MUST` | 情态动词 must 的用法 | 情态动词 | rename | high |
| 54 | 就近原则 | `ENG-GRAMMAR-AGREEMENT-PROXIMITY` | 主谓一致的就近原则 | 主谓一致 | rename | high |
| 55 | 比较级 | `ENG-GRAMMAR-ADJECTIVE-COMPARATIVE` | 形容词比较级 | 比较结构 | rename | high |
| 56 | 介词搭配 | `ENG-VOCAB-COLLOCATION` | 固定搭配 | 固定搭配 | merge | high |
| 57 | 事实细节 | `ENG-READING-DETAIL` | 细节理解 | 阅读理解 | rename | high |
| 58 | 主旨大意 | `ENG-READING-MAIN-IDEA` | 主旨大意 | 阅读理解 | keep | high |
| 59 | there be 句型 | `ENG-GRAMMAR-THERE-BE` | There be 句型 | 语法基础 | rename | high |
| 60 | 句子翻译 | `ENG-WRITING-SENTENCE-EXPRESSION` | 基础句子表达 | 书面表达 | rename | medium |

## 三、重点题目处理说明

### ID 41

- 当前标签：`动词辨析`
- 推荐标准标签：`ENG-VOCAB-COLLOCATION` / 固定搭配
- action：`merge`
- 判断依据：题目要求在 `pay / take / make / give` 中选择，但正确性取决于固定结构 `pay attention to`。核心不是四个动词的一般词义，而是固定搭配记忆。
- 合并关系：与ID 56统一到“固定搭配”。后续可以额外使用能力标签区分“动词搭配”和“介词搭配”，但不需要拆成两个掌握度知识点。

### ID 42

- 当前标签：`形容词辨析`
- 推荐标准标签：`ENG-VOCAB-CONTEXT-VERB` / 动词语境辨析
- action：`fix`
- 判断依据：四个选项 `follow / invite / borrow / raise` 均为动词，正确答案 `follow` 来自 `instructions are easy to follow` 的语义与搭配。当前“形容词辨析”与选项词性明显不符。
- 处理结论：纠正为“动词语境辨析”，不与ID 41合并，因为本题仍需要判断动词语义，不能只靠一个固定短语完成。

### ID 48

- 当前标签：`动名词`
- 推荐标准标签：`ENG-NONFINITE-INFINITIVE` / 动词不定式
- action：`fix`
- 判断依据：正确结构为 `a good way to improve your vocabulary`，答案和解析都明确使用 `to improve`。题目没有考查动名词。
- 合并关系：与ID 47复用同一个“动词不定式”标准编码。

### ID 60

- 当前标签：`句子翻译`
- 推荐标准标签：`ENG-WRITING-SENTENCE-EXPRESSION` / 基础句子表达
- action：`rename`
- confidence：`medium`
- 判断依据：“句子翻译”描述的是作答形式，不是稳定知识点。题目要求将中文信息组织成正确英文句子，主要训练基础句子表达。
- 注意事项：参考答案使用动名词短语作主语和主谓一致，但该中文句子也可能存在其他合理译法。因此不建议仅凭当前参考答案将其唯一归入“动名词作主语”。未来可把“句子翻译”保存为题型标签，把“动名词作主语”“主谓一致”等保存为次要知识点。

## 四、映射结果汇总

| 项目 | 数量 |
|---|---:|
| 题目映射总数 | 60 |
| 数学映射 | 20 |
| 物理映射 | 20 |
| 英语映射 | 20 |
| `keep` | 21 |
| `rename` | 35 |
| `merge` | 2 |
| `fix` | 2 |
| `high` confidence | 59 |
| `medium` confidence | 1 |
| 映射后的标准知识点编码 | 58 |

60个旧知识点映射为58个标准知识点，减少的两个来源于：

1. ID 41与ID 56合并为 `ENG-VOCAB-COLLOCATION`；
2. ID 48修正后与ID 47合并为 `ENG-NONFINITE-INFINITIVE`。

## 五、使用边界

1. 本映射表是后续迁移设计依据，不代表数据库已经变更。
2. 正式迁移前应由人工最终确认ID 41、42、48、60。
3. 后续新题必须优先复用本文件中的标准编码。
4. 新题只有在现有标准编码确实无法表达时，才允许申请新增知识点。
5. 中文标准名称可以优化，`standard knowledge_point_id`一旦正式使用应保持稳定。
