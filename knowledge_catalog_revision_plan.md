# kp-mapping-v1.1知识目录修订方案

方案日期：2026-07-23  
方案依据：`knowledge_point_mapping.md`、`knowledge_catalog_review.md`  
当前数据库版本：Revision B / `20260723_0007`  
执行状态：仅完成设计，尚未修改数据库、代码、迁移文件或题目，禁止在人工确认前执行Revision C。

## 一、修订目标

`kp-mapping-v1.1`重点解决：

1. 过细知识点难以稳定扩充5—10题；
2. 同一学习能力被拆成多个过窄掌握度节点；
3. 综合能力标签被误当作知识点；
4. 二级目录名称与编码范围不一致；
5. 在调整目录的同时，保证`kp-mapping-v1`旧code仍可识别。

本次不追求一次补齐完整高考目录，只修正当前58个三级知识点中已经明确的问题。

## 二、旧code兼容规则

每个`kp-mapping-v1`旧code在v1.1中必须属于以下状态之一：

| 状态 | 含义 | 后续行为 |
|---|---|---|
| `active` | 继续作为标准知识点使用 | 新题和旧题均可继续关联 |
| `redirected` | 被新知识点合并或扩大范围 | 不再建立新关联，读取旧code时重定向到新code |
| `ability_only` | 不再作为主要知识点 | 旧code保留可识别，语义迁移为能力标签 |
| `deprecated` | 保留历史兼容，但不再使用 | 不删除记录，不建立新关联 |

兼容原则：

1. 不物理删除任何v1旧code。
2. 已发布code不复用为其他含义。
3. 旧code解析必须得到唯一的新标准code或能力标签。
4. Revision C只关联v1.1中的`active`标准知识点。
5. 旧code即使停止使用，也应保留原名称、替代目标和停用原因。
6. 在未来数据库实施中，旧节点可以设置`is_active=false`，但不能删除。
7. 在当前模型尚无`replaced_by_code`字段时，重定向关系先冻结在版本化映射清单中，不临时修改表结构。

建议的解析顺序：

```text
输入code
  ↓
v1.1 active code → 直接返回
  ↓
旧code redirect表 → 返回replacement code
  ↓
ability_only → 返回能力标签，不作为知识画像节点
  ↓
未知code → 报错，禁止自动创建
```

## 三、需要合并的知识点

### 定语从句关系词

当前：

- `ENG-CLAUSE-RELATIVE-THAT`
- `ENG-CLAUSE-RELATIVE-WHERE`

合并为：

```text
ENG-CLAUSE-RELATIVE-WORD-SELECTION
定语从句关系词的选择
```

处理：

| 旧code | v1.1状态 | replacement |
|---|---|---|
| `ENG-CLAUSE-RELATIVE-THAT` | redirected | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` |
| `ENG-CLAUSE-RELATIVE-WHERE` | redirected | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` |

判断依据：

- 高中训练的核心不是分别记忆`that`和`where`，而是判断先行词、从句成分以及关系代词/关系副词。
- 合并后容易构建5—10道有区分度的题。
- 具体关系词可保留为内容标签：`relative_word=that`、`relative_word=where`。

## 四、需要扩大范围并替换code的知识点

### 1. 集合的交集

当前：

```text
MATH-SET-INTERSECTION
集合的基本运算（交集）
```

修订为：

```text
MATH-SET-OPERATIONS
集合的基本运算
```

- 旧code状态：`redirected`
- 内容标签：`operation=intersection`
- 扩展范围：并集、交集、补集及组合运算
- 当前题目ID 1未来关联新code。

### 2. 匀变速直线运动速度公式

当前：

```text
PHY-KINEMATICS-VELOCITY-EQUATION
匀变速直线运动速度公式
```

修订为：

```text
PHY-KINEMATICS-UNIFORM-ACCELERATION
匀变速直线运动规律
```

- 旧code状态：`redirected`
- 内容标签：`formula=velocity`
- 扩展范围：速度公式、位移公式、速度—位移关系及图像基础
- 当前题目ID 23未来关联新code。

### 3. 光的折射现象

当前：

```text
PHY-OPTICS-REFRACTION-PHENOMENON
光的折射现象
```

修订为：

```text
PHY-OPTICS-REFRACTION
光的折射规律
```

- 旧code状态：`redirected`
- 内容标签：`focus=phenomenon`
- 扩展范围：折射现象、折射方向、折射率和定性规律
- 当前题目ID 40未来关联新code。

### 4. 情态动词must

当前：

```text
ENG-GRAMMAR-MODAL-MUST
情态动词 must 的用法
```

修订为：

```text
ENG-GRAMMAR-MODAL-BASIC
情态动词的基本用法
```

- 旧code状态：`redirected`
- 内容标签：`modal=must`
- 扩展范围：must、can、may、should、could等基本语义和语境判断
- 当前题目ID 53未来关联新code。

## 五、降级为能力标签的节点

### 基础句子表达

当前：

```text
ENG-WRITING-SENTENCE-EXPRESSION
基础句子表达
```

问题：

- 它描述综合表达能力，不是边界清晰的知识点。
- 同一得分或错误可能来自词汇、非谓语、主谓一致或基本句型。
- 如果直接进入`knowledge_status`，掌握度无法解释具体学习漏洞。

v1.1处理：

| 项目 | 设计 |
|---|---|
| 旧code状态 | `ability_only` |
| 能力标签 | `sentence_expression` |
| 作答形式标签 | `translation` |
| 是否作为主要知识点 | 否 |
| 是否参与独立掌握度 | 否 |

题目ID 60的建议主要知识点：

```text
ENG-NONFINITE-GERUND-SUBJECT
动名词短语作主语
```

理由：

- 当前标准答案`Learning English requires patience.`明确使用动名词短语作主语。
- 该知识点可以稳定建设5—10道句型转换、语法填空和翻译题。
- “基础句子表达”和“句子翻译”仍保留为能力、作答形式标签。

风险：

- 题目存在其他合理译法，所以该映射置信度为`medium`。
- Revision C执行前必须人工确认题目ID 60是否采用此主要知识点。

## 六、仅修改中文名称、不更换code

以下节点语义不变，只统一显示名称：

| code | v1名称 | v1.1名称 | 原因 |
|---|---|---|---|
| `MATH-SET` | 集合与逻辑 | 集合 | 已有独立`MATH-LOGIC`模块，避免范围重叠 |
| `PHY-PROJECTILE` | 曲线运动 | 抛体运动 | 使显示名称与编码范围一致 |
| `PHY-WORK-ENERGY-WORK-CALCULATION` | 功的计算 | 功的概念与计算 | 与动能、动量命名方式更一致 |
| `ENG-GRAMMAR-VOICE-PRESENT-PASSIVE` | 一般现在时被动语态 | 一般现在时的被动语态 | 统一中文语法表达 |
| `ENG-GRAMMAR-THERE-BE` | There be 句型 | There be句型 | 统一中英混排格式 |

### 保留但记录的编码历史问题

`MATH-EXPONENT`显示名称为“指数与对数”，编码没有完整表达对数范围。v1.1建议：

- 暂不更换该二级模块code；
- 保持`MATH-EXPONENT`兼容；
- 在目录说明中明确其范围包含指数与对数；
- 不为纯粹追求命名对称而制造新的父级重定向。

这是稳定性优先于编码美观的选择。

## 七、保持不变的三级知识点

以下48个三级知识点在v1.1中保持`active`，code与语义均不变。

### 数学19个

- `MATH-LOGIC-SUFFICIENT-NECESSARY`
- `MATH-FUNCTION-DOMAIN`
- `MATH-FUNCTION-MONOTONICITY`
- `MATH-FUNCTION-PARITY`
- `MATH-EXPONENT-OPERATION`
- `MATH-LOGARITHM-OPERATION`
- `MATH-TRIG-SPECIAL-ANGLE`
- `MATH-TRIG-FUNDAMENTAL-IDENTITY`
- `MATH-VECTOR-COORDINATE`
- `MATH-SEQUENCE-ARITHMETIC-GENERAL`
- `MATH-SEQUENCE-GEOMETRIC-GENERAL`
- `MATH-INEQUALITY-QUADRATIC`
- `MATH-SOLID-LINE-PLANE-PERPENDICULAR`
- `MATH-ANALYTIC-LINE-SLOPE`
- `MATH-ANALYTIC-CIRCLE-STANDARD`
- `MATH-PROBABILITY-CLASSICAL`
- `MATH-STATISTICS-MEAN`
- `MATH-DERIVATIVE-ELEMENTARY`
- `MATH-COMPLEX-ARITHMETIC`

数学仅替换`MATH-SET-INTERSECTION`，其余19个保持。

### 物理18个

- `PHY-MOTION-PARTICLE-MODEL`
- `PHY-MOTION-DISPLACEMENT-DISTANCE`
- `PHY-KINEMATICS-FREE-FALL`
- `PHY-FORCE-COMPOSITION`
- `PHY-NEWTON-THIRD-LAW`
- `PHY-NEWTON-SECOND-LAW`
- `PHY-PROJECTILE-HORIZONTAL`
- `PHY-CIRCULAR-CENTRIPETAL-ACCELERATION`
- `PHY-GRAVITY-UNIVERSAL-LAW`
- `PHY-WORK-ENERGY-WORK-CALCULATION`
- `PHY-WORK-ENERGY-KINETIC`
- `PHY-MOMENTUM-BASIC`
- `PHY-ELECTROSTATICS-COULOMB-LAW`
- `PHY-CIRCUIT-OHM-LAW`
- `PHY-CIRCUIT-ELECTRIC-POWER`
- `PHY-MAGNETIC-FIELD-DIRECTION`
- `PHY-INDUCTION-CURRENT-CONDITION`
- `PHY-WAVE-SPEED-FREQUENCY-WAVELENGTH`

物理替换速度公式和折射现象两个节点，其余18个保持。

### 英语14个

- `ENG-VOCAB-COLLOCATION`
- `ENG-VOCAB-CONTEXT-VERB`
- `ENG-GRAMMAR-TENSE-PRESENT-SIMPLE`
- `ENG-GRAMMAR-TENSE-PRESENT-PERFECT`
- `ENG-GRAMMAR-TENSE-PAST-CONTINUOUS`
- `ENG-GRAMMAR-VOICE-PRESENT-PASSIVE`
- `ENG-NONFINITE-INFINITIVE`
- `ENG-CLAUSE-OBJECT-WORD-ORDER`
- `ENG-CLAUSE-ADVERBIAL-CONDITION`
- `ENG-GRAMMAR-AGREEMENT-PROXIMITY`
- `ENG-GRAMMAR-ADJECTIVE-COMPARATIVE`
- `ENG-READING-DETAIL`
- `ENG-READING-MAIN-IDEA`
- `ENG-GRAMMAR-THERE-BE`

英语有2个关系词节点合并、1个must节点扩大、1个表达节点降级，其余14个保持。

### 正确汇总

| 学科 | v1三级点 | 原code保持active | redirected | ability_only | v1.1新增标准code |
|---|---:|---:|---:|---:|---:|
| 数学 | 20 | 19 | 1 | 0 | 1 |
| 物理 | 20 | 18 | 2 | 0 | 2 |
| 英语 | 18 | 14 | 3 | 1 | 3 |
| 合计 | 58 | 51 | 6 | 1 | 6 |

v1.1启用的三级标准知识点数量：

```text
51个原code继续启用
+ 6个新标准code
= 57个active三级知识点
```

数据库中旧节点仍然保留，因此未来实施v1.1后：

- 知识点历史记录总数不会因修订而减少；
- 旧code仍可查询；
- active三级知识点为57个；
- 历史三级节点加新增节点共64条，其中7条为重定向或能力标签状态。

## 八、v1到v1.1重定向清单

| v1旧code | v1.1状态 | replacement或能力标签 |
|---|---|---|
| `MATH-SET-INTERSECTION` | redirected | `MATH-SET-OPERATIONS` |
| `PHY-KINEMATICS-VELOCITY-EQUATION` | redirected | `PHY-KINEMATICS-UNIFORM-ACCELERATION` |
| `PHY-OPTICS-REFRACTION-PHENOMENON` | redirected | `PHY-OPTICS-REFRACTION` |
| `ENG-CLAUSE-RELATIVE-THAT` | redirected | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` |
| `ENG-CLAUSE-RELATIVE-WHERE` | redirected | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` |
| `ENG-GRAMMAR-MODAL-MUST` | redirected | `ENG-GRAMMAR-MODAL-BASIC` |
| `ENG-WRITING-SENTENCE-EXPRESSION` | ability_only | `sentence_expression` |

新增但不是旧code直接重命名：

```text
ENG-NONFINITE-GERUND-SUBJECT
```

用于承接题目ID 60的主要知识点，等待人工确认。

## 九、Revision C映射影响

如果v1.1获得确认，Revision C应按以下方式关联受影响题目：

| 题目ID | v1计划 | v1.1计划 |
|---:|---|---|
| 1 | `MATH-SET-INTERSECTION` | `MATH-SET-OPERATIONS` |
| 23 | `PHY-KINEMATICS-VELOCITY-EQUATION` | `PHY-KINEMATICS-UNIFORM-ACCELERATION` |
| 40 | `PHY-OPTICS-REFRACTION-PHENOMENON` | `PHY-OPTICS-REFRACTION` |
| 49 | `ENG-CLAUSE-RELATIVE-THAT` | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` |
| 50 | `ENG-CLAUSE-RELATIVE-WHERE` | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` |
| 53 | `ENG-GRAMMAR-MODAL-MUST` | `ENG-GRAMMAR-MODAL-BASIC` |
| 60 | `ENG-WRITING-SENTENCE-EXPRESSION` | `ENG-NONFINITE-GERUND-SUBJECT`，待确认 |

其余53道题沿用v1映射的标准code，仅部分中文显示名称发生变化。

## 十、人工确认清单

执行任何数据库修订或Revision C前，需要明确回答：

1. 是否批准合并that/where为“定语从句关系词的选择”？
2. 是否批准将集合交集扩大为“集合的基本运算”？
3. 是否批准将速度公式扩大为“匀变速直线运动规律”？
4. 是否批准将折射现象扩大为“光的折射规律”？
5. 是否批准将must扩大为“情态动词的基本用法”？
6. 是否批准将“基础句子表达”降级为能力标签？
7. 是否批准题目ID 60主要关联“动名词短语作主语”？
8. 是否批准二级模块“集合与逻辑”改名为“集合”？
9. 是否批准二级模块“曲线运动”改名为“抛体运动”？
10. 是否接受`MATH-EXPONENT`作为历史稳定code继续表示“指数与对数”？

未获得上述确认前：

- 不修改Revision B数据；
- 不新增v1.1知识点；
- 不停用旧code；
- 不修改任何显示名称；
- 不执行Revision C。
