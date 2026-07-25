# Phase 10.3 第一批50题人工审核表

审核日期：____________  
审核人：____________  
复核人：____________  
题库批次：`phase10_3_batch01`  
当前状态：`DRAFT / 未批准 / 未导入`

## 一、使用方法

按以下顺序审核，不能跳过独立作答：

1. 打开对应 draft JSON，只阅读题干和选项。
2. 暂时不要查看 `answer` 和 `solution`。
3. 在本表填写“独立答案”。
4. 完成一个学科后，再展开文末的标准答案核对区。
5. 检查题干、选项、解析、知识点、难度和来源。
6. 填写最终结论：
   - `PASS`：可以进入首批候选。
   - `REVISE`：必须修改后重新审核。
   - `REJECT`：不适合进入题库。

审核文件：

- [数学20题](../data/question_bank/drafts/phase10_3_math_core_batch01_v1.json)
- [物理15题](../data/question_bank/drafts/phase10_3_physics_core_batch01_v1.json)
- [英语15题](../data/question_bank/drafts/phase10_3_english_core_batch01_v1.json)

## 二、首批15题建议

第一轮优先审核以下题目，每科5题：

```text
数学：M01、M04、M09、M16、M19
物理：P01、P04、P08、P11、P14
英语：E01、E04、E06、E10、E14
```

这15题覆盖不同核心主题和难度。只有全部完成审核，才能讨论小批导入。

## 三、第一阶段：独立作答

### 数学20题

| 编号 | 题目标题 | 知识点code | 难度 | 独立答案 | 计算/判断过程简记 | 完成 |
|---|---|---|---:|---|---|---|
| M01 | 根式函数定义域 | `MATH-FUNCTION-DOMAIN` | 2 |  |  | ☐ |
| M02 | 分式函数定义域 | `MATH-FUNCTION-DOMAIN` | 2 |  |  | ☐ |
| M03 | 根式与分式复合定义域 | `MATH-FUNCTION-DOMAIN` | 3 |  |  | ☐ |
| M04 | 一次函数单调性 | `MATH-FUNCTION-MONOTONICITY` | 1 |  |  | ☐ |
| M05 | 二次函数递减区间 | `MATH-FUNCTION-MONOTONICITY` | 2 |  |  | ☐ |
| M06 | 由单调性求参数范围 | `MATH-FUNCTION-MONOTONICITY` | 3 |  |  | ☐ |
| M07 | 奇函数辨析 | `MATH-FUNCTION-PARITY` | 2 |  |  | ☐ |
| M08 | 利用偶函数性质求值 | `MATH-FUNCTION-PARITY` | 3 |  |  | ☐ |
| M09 | 等差数列通项直接计算 | `MATH-SEQUENCE-ARITHMETIC-GENERAL` | 1 |  |  | ☐ |
| M10 | 由两项求等差数列公差 | `MATH-SEQUENCE-ARITHMETIC-GENERAL` | 2 |  |  | ☐ |
| M11 | 等差数列中项性质 | `MATH-SEQUENCE-ARITHMETIC-GENERAL` | 3 |  |  | ☐ |
| M12 | 等比数列通项直接计算 | `MATH-SEQUENCE-GEOMETRIC-GENERAL` | 2 |  |  | ☐ |
| M13 | 由两项求正项等比数列公比 | `MATH-SEQUENCE-GEOMETRIC-GENERAL` | 3 |  |  | ☐ |
| M14 | 正弦特殊角求值 | `MATH-TRIG-SPECIAL-ANGLE` | 1 |  |  | ☐ |
| M15 | 特殊角三角函数综合求值 | `MATH-TRIG-SPECIAL-ANGLE` | 2 |  |  | ☐ |
| M16 | 由正弦值求余弦值 | `MATH-TRIG-FUNDAMENTAL-IDENTITY` | 2 |  |  | ☐ |
| M17 | 正切与正余弦关系 | `MATH-TRIG-FUNDAMENTAL-IDENTITY` | 3 |  |  | ☐ |
| M18 | 幂函数求导 | `MATH-DERIVATIVE-ELEMENTARY` | 1 |  |  | ☐ |
| M19 | 多项式导数在点处的值 | `MATH-DERIVATIVE-ELEMENTARY` | 2 |  |  | ☐ |
| M20 | 利用导数求切线斜率 | `MATH-DERIVATIVE-ELEMENTARY` | 3 |  |  | ☐ |

### 物理15题

| 编号 | 题目标题 | 知识点code | 难度 | 独立答案 | 计算/判断过程简记 | 完成 |
|---|---|---|---:|---|---|---|
| P01 | 匀加速运动末速度 | `PHY-KINEMATICS-UNIFORM-ACCELERATION` | 1 |  |  | ☐ |
| P02 | 匀加速运动位移 | `PHY-KINEMATICS-UNIFORM-ACCELERATION` | 2 |  |  | ☐ |
| P03 | 匀减速停车时间 | `PHY-KINEMATICS-UNIFORM-ACCELERATION` | 3 |  |  | ☐ |
| P04 | 自由落体末速度 | `PHY-KINEMATICS-FREE-FALL` | 2 |  |  | ☐ |
| P05 | 自由落体下落时间 | `PHY-KINEMATICS-FREE-FALL` | 3 |  |  | ☐ |
| P06 | 同向共线力合成 | `PHY-FORCE-COMPOSITION` | 1 |  |  | ☐ |
| P07 | 反向共线力合成 | `PHY-FORCE-COMPOSITION` | 2 |  |  | ☐ |
| P08 | 垂直力的合成 | `PHY-FORCE-COMPOSITION` | 3 |  |  | ☐ |
| P09 | 由合力求加速度 | `PHY-NEWTON-SECOND-LAW` | 1 |  |  | ☐ |
| P10 | 由质量和加速度求合力 | `PHY-NEWTON-SECOND-LAW` | 2 |  |  | ☐ |
| P11 | 考虑摩擦力的牛顿第二定律 | `PHY-NEWTON-SECOND-LAW` | 3 |  |  | ☐ |
| P12 | 速度变化与动能之比 | `PHY-WORK-ENERGY-KINETIC` | 2 |  |  | ☐ |
| P13 | 恒力做功计算 | `PHY-WORK-ENERGY-WORK-CALCULATION` | 2 |  |  | ☐ |
| P14 | 摩擦力负功 | `PHY-WORK-ENERGY-WORK-CALCULATION` | 3 |  |  | ☐ |
| P15 | 动能直接计算 | `PHY-WORK-ENERGY-KINETIC` | 2 |  |  | ☐ |

### 英语15题

| 编号 | 题目标题 | 知识点code | 难度 | 独立答案 | 判断依据简记 | 完成 |
|---|---|---|---:|---|---|---|
| E01 | decide后接动词不定式 | `ENG-NONFINITE-INFINITIVE` | 1 |  |  | ☐ |
| E02 | encourage宾补中的不定式 | `ENG-NONFINITE-INFINITIVE` | 2 |  |  | ☐ |
| E03 | 形式主语句型中的不定式 | `ENG-NONFINITE-INFINITIVE` | 3 |  |  | ☐ |
| E04 | 动名词短语作主语 | `ENG-NONFINITE-GERUND-SUBJECT` | 2 |  |  | ☐ |
| E05 | 动名词主语与主谓一致 | `ENG-NONFINITE-GERUND-SUBJECT` | 3 |  |  | ☐ |
| E06 | 关系代词that的选择 | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 2 |  |  | ☐ |
| E07 | 关系副词where的选择 | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 2 |  |  | ☐ |
| E08 | 关系代词whose的选择 | `ENG-CLAUSE-RELATIVE-WORD-SELECTION` | 3 |  |  | ☐ |
| E09 | since引导的现在完成时 | `ENG-GRAMMAR-TENSE-PRESENT-PERFECT` | 2 |  |  | ☐ |
| E10 | 经历用法的现在完成时 | `ENG-GRAMMAR-TENSE-PRESENT-PERFECT` | 2 |  |  | ☐ |
| E11 | 强调现在结果的完成时 | `ENG-GRAMMAR-TENSE-PRESENT-PERFECT` | 3 |  |  | ☐ |
| E12 | 学习间隔时间细节 | `ENG-READING-DETAIL` | 2 |  |  | ☐ |
| E13 | 科学社团准备事项细节 | `ENG-READING-DETAIL` | 3 |  |  | ☐ |
| E14 | 词汇笔记方法主旨 | `ENG-READING-MAIN-IDEA` | 2 |  |  | ☐ |
| E15 | 短时运动与学习主旨 | `ENG-READING-MAIN-IDEA` | 3 |  |  | ☐ |

## 四、第二阶段：标准答案核对

先完成上面的独立作答，再展开本节。

<details>
<summary>点击展开标准答案</summary>

### 数学答案

| 编号 | 标准答案 | 独立答案一致 | 若不一致，原因 |
|---|---|---|---|
| M01 | B | ☐是 ☐否 |  |
| M02 | D | ☐是 ☐否 |  |
| M03 | B | ☐是 ☐否 |  |
| M04 | B | ☐是 ☐否 |  |
| M05 | A | ☐是 ☐否 |  |
| M06 | A | ☐是 ☐否 |  |
| M07 | B | ☐是 ☐否 |  |
| M08 | D | ☐是 ☐否 |  |
| M09 | C | ☐是 ☐否 |  |
| M10 | B | ☐是 ☐否 |  |
| M11 | C | ☐是 ☐否 |  |
| M12 | C | ☐是 ☐否 |  |
| M13 | B | ☐是 ☐否 |  |
| M14 | B | ☐是 ☐否 |  |
| M15 | C | ☐是 ☐否 |  |
| M16 | D | ☐是 ☐否 |  |
| M17 | C | ☐是 ☐否 |  |
| M18 | C | ☐是 ☐否 |  |
| M19 | C | ☐是 ☐否 |  |
| M20 | B | ☐是 ☐否 |  |

### 物理答案

| 编号 | 标准答案 | 独立答案一致 | 若不一致，原因 |
|---|---|---|---|
| P01 | C | ☐是 ☐否 |  |
| P02 | C | ☐是 ☐否 |  |
| P03 | B | ☐是 ☐否 |  |
| P04 | C | ☐是 ☐否 |  |
| P05 | B | ☐是 ☐否 |  |
| P06 | C | ☐是 ☐否 |  |
| P07 | A | ☐是 ☐否 |  |
| P08 | B | ☐是 ☐否 |  |
| P09 | B | ☐是 ☐否 |  |
| P10 | C | ☐是 ☐否 |  |
| P11 | B | ☐是 ☐否 |  |
| P12 | C | ☐是 ☐否 |  |
| P13 | C | ☐是 ☐否 |  |
| P14 | A | ☐是 ☐否 |  |
| P15 | C | ☐是 ☐否 |  |

### 英语答案

| 编号 | 标准答案 | 独立答案一致 | 若不一致，原因 |
|---|---|---|---|
| E01 | B | ☐是 ☐否 |  |
| E02 | B | ☐是 ☐否 |  |
| E03 | B | ☐是 ☐否 |  |
| E04 | C | ☐是 ☐否 |  |
| E05 | B | ☐是 ☐否 |  |
| E06 | B | ☐是 ☐否 |  |
| E07 | C | ☐是 ☐否 |  |
| E08 | C | ☐是 ☐否 |  |
| E09 | C | ☐是 ☐否 |  |
| E10 | C | ☐是 ☐否 |  |
| E11 | C | ☐是 ☐否 |  |
| E12 | A | ☐是 ☐否 |  |
| E13 | B | ☐是 ☐否 |  |
| E14 | A | ☐是 ☐否 |  |
| E15 | B | ☐是 ☐否 |  |

</details>

任一题独立答案与标准答案不一致，必须标记为 `REVISE`，重新计算或请第二人复核，不能
直接以 JSON 中的答案为准。

## 五、第三阶段：逐题质量复核

每道题均检查以下六项：

| 检查项 | 通过标准 |
|---|---|
| 题干 | 条件完整、无歧义、无缺失图片或材料 |
| 选项 | 只有一个正确答案、无重复、无格式暗示 |
| 解析 | 说明关键规则与步骤，不只重复答案 |
| 知识点 | 唯一primary，code正确且粒度合适 |
| 难度 | 与准高三学生实际认知负担相符 |
| 来源 | 标识为原创批次，无隐私或版权风险 |

### 数学质量结论

| 编号 | 题干 | 选项 | 解析 | 知识点 | 难度 | 结论 | 修改意见 |
|---|---|---|---|---|---|---|---|
| M01 |  |  |  |  |  |  |  |
| M02 |  |  |  |  |  |  |  |
| M03 |  |  |  |  |  |  |  |
| M04 |  |  |  |  |  |  |  |
| M05 |  |  |  |  |  |  |  |
| M06 |  |  |  |  |  |  |  |
| M07 |  |  |  |  |  |  |  |
| M08 |  |  |  |  |  |  |  |
| M09 |  |  |  |  |  |  |  |
| M10 |  |  |  |  |  |  |  |
| M11 |  |  |  |  |  |  |  |
| M12 |  |  |  |  |  |  |  |
| M13 |  |  |  |  |  |  |  |
| M14 |  |  |  |  |  |  |  |
| M15 |  |  |  |  |  |  |  |
| M16 |  |  |  |  |  |  |  |
| M17 |  |  |  |  |  |  |  |
| M18 |  |  |  |  |  |  |  |
| M19 |  |  |  |  |  |  |  |
| M20 |  |  |  |  |  |  |  |

### 物理质量结论

| 编号 | 题干 | 选项 | 解析 | 知识点 | 难度 | 结论 | 修改意见 |
|---|---|---|---|---|---|---|---|
| P01 |  |  |  |  |  |  |  |
| P02 |  |  |  |  |  |  |  |
| P03 |  |  |  |  |  |  |  |
| P04 |  |  |  |  |  |  |  |
| P05 |  |  |  |  |  |  |  |
| P06 |  |  |  |  |  |  |  |
| P07 |  |  |  |  |  |  |  |
| P08 |  |  |  |  |  |  |  |
| P09 |  |  |  |  |  |  |  |
| P10 |  |  |  |  |  |  |  |
| P11 |  |  |  |  |  |  |  |
| P12 |  |  |  |  |  |  |  |
| P13 |  |  |  |  |  |  |  |
| P14 |  |  |  |  |  |  |  |
| P15 |  |  |  |  |  |  |  |

### 英语质量结论

| 编号 | 题干 | 选项 | 解析 | 知识点 | 难度 | 结论 | 修改意见 |
|---|---|---|---|---|---|---|---|
| E01 |  |  |  |  |  |  |  |
| E02 |  |  |  |  |  |  |  |
| E03 |  |  |  |  |  |  |  |
| E04 |  |  |  |  |  |  |  |
| E05 |  |  |  |  |  |  |  |
| E06 |  |  |  |  |  |  |  |
| E07 |  |  |  |  |  |  |  |
| E08 |  |  |  |  |  |  |  |
| E09 |  |  |  |  |  |  |  |
| E10 |  |  |  |  |  |  |  |
| E11 |  |  |  |  |  |  |  |
| E12 |  |  |  |  |  |  |  |
| E13 |  |  |  |  |  |  |  |
| E14 |  |  |  |  |  |  |  |
| E15 |  |  |  |  |  |  |  |

建议填写方式：

```text
题干/选项/解析/知识点：PASS 或 REVISE
难度：PASS 或建议改为1/2/3/4/5
结论：PASS / REVISE / REJECT
```

## 六、批次审核汇总

| 项目 | 数量 |
|---|---:|
| 总题数 | 50 |
| 已完成独立作答 |  |
| 答案一致 |  |
| PASS |  |
| REVISE |  |
| REJECT |  |
| 待第二人复核 |  |

学科汇总：

| 学科 | 总数 | PASS | REVISE | REJECT | 是否允许进入候选 |
|---|---:|---:|---:|---:|---|
| 数学 | 20 |  |  |  |  |
| 物理 | 15 |  |  |  |  |
| 英语 | 15 |  |  |  |  |

审核结论：

```text
☐ 本批次仍在审核，禁止导入
☐ 仅批准首批15题进入小批导入准备
☐ 批准其他明确列出的题目
```

批准题目编号：__________________________________________________  
必须修改题目编号：______________________________________________  
拒绝题目编号：__________________________________________________  
审核人签字：________________  
复核人签字：________________  
日期：________________

## 七、批准后的必做检查

修改任意题目后，重新运行：

```powershell
python -m app.cli.question_bank lint `
  data/question_bank/drafts/phase10_3_math_core_batch01_v1.json `
  data/question_bank/drafts/phase10_3_physics_core_batch01_v1.json `
  data/question_bank/drafts/phase10_3_english_core_batch01_v1.json

python -m app.cli.question_bank verify `
  data/question_bank/drafts/phase10_3_math_core_batch01_v1.json `
  data/question_bank/drafts/phase10_3_physics_core_batch01_v1.json `
  data/question_bank/drafts/phase10_3_english_core_batch01_v1.json
```

必须满足：

- 50题或批准子集全部通过；
- Error为0；
- 数据库重复为0；
- 人工审核表已填写；
- 负责人另行确认后才允许导入。
