# Revision C Dry Run报告

报告日期：2026-07-23  
映射版本：`kp-mapping-v1.1`  
数据来源：`knowledge_catalog_revision_plan.md`、`knowledge_point_mapping.md`、PostgreSQL当前60道题和Revision B知识目录。  
执行方式：只读检查。未修改数据库、代码、题目或迁移文件，未执行Revision C。

## 一、Dry Run结论

| 检查项 | 结果 |
|---|---|
| 当前题目数 | 60 |
| 生成primary关联数 | 60 |
| 缺少primary的题目 | 0 |
| 重复题目ID | 0 |
| 最终使用的不同三级code | 57 |
| 当前Revision B已存在的最终code | 51 |
| v1.1计划新增、当前尚不存在的code | 6 |
| 跨学科关联 | 0 |
| high confidence | 59 |
| medium confidence | 1 |
| secondary关联 | 0，本次不自动推断 |
| 是否可以立即执行Revision C | 否 |

阻断原因：

1. 6个`kp-mapping-v1.1`新code尚未写入`knowledge_points`。
2. ID 60映射到“动名词短语作主语”仍需人工确认。
3. `kp-mapping-v1.1`的目录修订尚未获得完整人工批准。

## 二、60道题最终关联表

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
| 27 | 牛顿第二定律 | `PHY-NEWTON-SECOND-LAW` | 牛顿第二定律 | primary | keep | 题目直接应用F=ma | high |
| 28 | 平抛运动 | `PHY-PROJECTILE-HORIZONTAL` | 平抛运动规律 | primary | rename | 题目考查平抛水平方向运动规律 | high |
| 29 | 向心加速度 | `PHY-CIRCULAR-CENTRIPETAL-ACCELERATION` | 向心加速度 | primary | keep | 题目直接考查向心加速度公式 | high |
| 30 | 万有引力定律 | `PHY-GRAVITY-UNIVERSAL-LAW` | 万有引力定律 | primary | keep | 题目考查万有引力比例关系 | high |
| 31 | 功 | `PHY-WORK-ENERGY-WORK-CALCULATION` | 功的概念与计算 | primary | rename | 统一粒度并覆盖功的含义与计算 | high |
| 32 | 动能 | `PHY-WORK-ENERGY-KINETIC` | 动能概念与计算 | primary | rename | 避免使用过宽的单词标签 | high |
| 33 | 动量 | `PHY-MOMENTUM-BASIC` | 动量概念与计算 | primary | rename | 避免与二级模块同名 | high |
| 34 | 库仑定律 | `PHY-ELECTROSTATICS-COULOMB-LAW` | 库仑定律 | primary | keep | 题目考查同种电荷相斥 | high |
| 35 | 欧姆定律 | `PHY-CIRCUIT-OHM-LAW` | 欧姆定律 | primary | keep | 题目直接应用R=U/I | high |
| 36 | 电功率 | `PHY-CIRCUIT-ELECTRIC-POWER` | 电功率的计算 | primary | rename | 明确训练目标为电功率计算 | high |
| 37 | 磁场方向 | `PHY-MAGNETIC-FIELD-DIRECTION` | 磁场方向的判定 | primary | rename | 题目考查磁场方向定义与判定 | high |
| 38 | 感应电流条件 | `PHY-INDUCTION-CURRENT-CONDITION` | 感应电流的产生条件 | primary | rename | 使用标准物理表述 | high |
| 39 | 波速公式 | `PHY-WAVE-SPEED-FREQUENCY-WAVELENGTH` | 波速、波长与频率的关系 | primary | rename | 从公式名称提升为三个物理量关系 | high |
| 40 | 光的折射 | `PHY-OPTICS-REFRACTION` | 光的折射规律 | primary | broaden | 折射现象纳入可扩充的折射规律知识点 | high |

### 英语

| question_id | old_knowledge_point | new_knowledge_point_code | standard_name | role | action | reason | confidence |
|---:|---|---|---|---|---|---|---|
| 41 | 动词辨析 | `ENG-VOCAB-COLLOCATION` | 固定搭配 | primary | fix | 正确性来自`pay attention to`固定搭配 | high |
| 42 | 形容词辨析 | `ENG-VOCAB-CONTEXT-VERB` | 动词语境辨析 | primary | fix | 四个选项均为动词，原词性标签错误 | high |
| 43 | 一般现在时 | `ENG-GRAMMAR-TENSE-PRESENT-SIMPLE` | 一般现在时 | primary | keep | `every Sunday`明确考查一般现在时 | high |
| 44 | 现在完成时 | `ENG-GRAMMAR-TENSE-PRESENT-PERFECT` | 现在完成时 | primary | keep | `twice`和语境明确指向现在完成时 | high |
| 45 | 过去进行时 | `ENG-GRAMMAR-TENSE-PAST-CONTINUOUS` | 过去进行时 | primary | keep | 过去具体时刻正在发生的动作 | high |
| 46 | 一般现在时的被动语态 | `ENG-GRAMMAR-VOICE-PRESENT-PASSIVE` | 一般现在时的被动语态 | primary | rename | code不变，仅统一中文名称 | high |
| 47 | 动词不定式 | `ENG-NONFINITE-INFINITIVE` | 动词不定式 | primary | keep | `decide to do`明确考查不定式 | high |
| 48 | 动名词 | `ENG-NONFINITE-INFINITIVE` | 动词不定式 | primary | fix | `a way to do`实际考查不定式，原标签错误 | high |
| 49 | 关系代词 that | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 定语从句关系词的选择 | primary | merge | 合并为关系词整体选择能力，that保留为内容标签 | high |
| 50 | 关系副词 where | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 定语从句关系词的选择 | primary | merge | 与that题共同训练从句成分和关系词选择 | high |
| 51 | 宾语从句语序 | `ENG-CLAUSE-OBJECT-WORD-ORDER` | 宾语从句的语序 | primary | rename | 统一中文表达 | high |
| 52 | 条件状语从句 | `ENG-CLAUSE-ADVERBIAL-CONDITION` | 条件状语从句 | primary | keep | 题目考查条件从句“主将从现” | high |
| 53 | 情态动词 must | `ENG-GRAMMAR-MODAL-BASIC` | 情态动词的基本用法 | primary | broaden | must纳入情态动词基本语义和语境判断 | high |
| 54 | 就近原则 | `ENG-GRAMMAR-AGREEMENT-PROXIMITY` | 主谓一致的就近原则 | primary | rename | 补充所属语法范围 | high |
| 55 | 比较级 | `ENG-GRAMMAR-ADJECTIVE-COMPARATIVE` | 形容词比较级 | primary | rename | 明确考查词类 | high |
| 56 | 介词搭配 | `ENG-VOCAB-COLLOCATION` | 固定搭配 | primary | merge | `be interested in`归入固定搭配，与ID 41复用画像节点 | high |
| 57 | 事实细节 | `ENG-READING-DETAIL` | 细节理解 | primary | rename | 使用高考阅读常用名称 | high |
| 58 | 主旨大意 | `ENG-READING-MAIN-IDEA` | 主旨大意 | primary | keep | 题目直接判断文章主旨 | high |
| 59 | there be 句型 | `ENG-GRAMMAR-THERE-BE` | There be句型 | primary | rename | code不变，统一显示格式 | high |
| 60 | 句子翻译 | `ENG-NONFINITE-GERUND-SUBJECT` | 动名词短语作主语 | primary | reclassify | 句子翻译降为能力标签；参考答案使用动名词短语作主语 | medium |

## 三、primary完整性检查

| 检查 | 结果 |
|---|---|
| 题目ID 1—60是否全部出现 | 是 |
| 是否每题恰好一个primary | 是 |
| 是否有题目没有primary | 否 |
| 是否有题目存在多个primary | 否 |
| 是否自动创建secondary | 否 |

Dry Run采用“每题一个primary”的保守策略。具体关系词、公式、交集、must和翻译形式暂时只记录在设计理由中，不在Revision C自动创建secondary关联。

## 四、code存在性检查

### 当前Revision B已存在

最终使用的57个不同code中，51个已存在于当前`knowledge_points`，且均满足：

- `level=3`
- `is_active=true`
- 学科与题目一致

### 当前尚不存在

以下6个code属于`kp-mapping-v1.1`计划新增项，当前Revision B数据库中不存在：

| 缺失code | 标准名称 | 影响题目 |
|---|---|---|
| `MATH-SET-OPERATIONS` | 集合的基本运算 | 1 |
| `PHY-KINEMATICS-UNIFORM-ACCELERATION` | 匀变速直线运动规律 | 23 |
| `PHY-OPTICS-REFRACTION` | 光的折射规律 | 40 |
| `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 定语从句关系词的选择 | 49、50 |
| `ENG-GRAMMAR-MODAL-BASIC` | 情态动词的基本用法 | 53 |
| `ENG-NONFINITE-GERUND-SUBJECT` | 动名词短语作主语 | 60 |

结论：如果现在直接执行Revision C，将有7道题因外键目标不存在而失败。必须先由独立的目录修订完成v1.1新code初始化，再执行题目关联。

## 五、跨学科检查

使用题目`subject`、code前缀和知识点所属学科进行三方比对：

| 学科 | 题目数量 | 预期前缀 | 不匹配 |
|---|---:|---|---:|
| 数学 | 20 | `MATH-` | 0 |
| 物理 | 20 | `PHY-` | 0 |
| 英语 | 20 | `ENG-` | 0 |

不存在跨学科关联。

## 六、人工确认问题

### 阻断项

#### ID 60

- 当前旧标签：句子翻译
- v1.1计划：`ENG-NONFINITE-GERUND-SUBJECT`
- 置信度：medium
- 风险：参考答案使用动名词短语作主语，但原中文存在其他合理译法。
- 必须确认：
  1. 是否接受以当前标准答案所体现的语法结构作为主要知识点；
  2. 是否将`sentence_expression`作为能力标签；
  3. 是否将`translation`作为作答形式标签。

在人工确认前，ID 60不得写入Revision C正式映射。

### 已有充分依据，但建议复核记录

| 题目ID | 调整 | Dry Run判断 |
|---:|---|---|
| 41 | 动词辨析 → 固定搭配 | high，`pay attention to`依据明确 |
| 42 | 形容词辨析 → 动词语境辨析 | high，选项全部为动词 |
| 48 | 动名词 → 动词不定式 | high，答案为`to improve` |
| 49、50 | that/where → 定语从句关系词选择 | high，但需批准合并策略 |

### 目录级人工确认

Revision C前还需批准：

1. 集合交集扩大为集合基本运算；
2. 速度公式扩大为匀变速直线运动规律；
3. 折射现象扩大为光的折射规律；
4. must扩大为情态动词基本用法；
5. that/where合并；
6. 基础句子表达降级为能力标签；
7. ID 60使用动名词短语作主语；
8. v1.1显示名称调整；
9. 旧code重定向兼容策略。

## 七、Dry Run统计

### 逐行唯一action统计

| action | 数量 |
|---|---:|
| keep | 21 |
| rename | 28 |
| fix | 3 |
| merge | 3 |
| broaden | 4 |
| reclassify | 1 |
| 合计 | 60 |

### confidence统计

| confidence | 数量 |
|---|---:|
| high | 59 |
| medium | 1 |
| low | 0 |

## 八、执行门槛

只有同时满足以下条件，Revision C才能进入开发：

1. 人工批准`kp-mapping-v1.1`。
2. 人工确认ID 60。
3. 6个新code已经通过独立目录修订写入数据库。
4. 旧code兼容规则已经冻结。
5. 再次运行Dry Run时不存在缺失code。
6. 60题全部恰好一个primary。
7. 跨学科关联仍为0。
8. `questions`的ID、学科、章节和旧知识点与本报告一致。

当前状态：

```text
Revision C readiness: BLOCKED
原因：6个目标code尚不存在，ID 60尚待人工确认。
```
