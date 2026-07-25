# Revision D Dry Run 报告

报告日期：2026-07-23  
映射版本：`kp-mapping-v1.1`  
数据库版本：`20260723_0009`  
执行范围：只读分析 `knowledge_status`。未修改数据库，未创建 Alembic migration，未执行 Revision D。

## 一、结论

| 检查项 | 结果 |
|---|---:|
| 当前 `knowledge_status` 记录 | 18 |
| 当前已填写 `knowledge_point_id` | 0 |
| 可安全映射 | 18 |
| 无法映射 | 0 |
| 涉及的不同目标 code | 12 |
| 同一用户合并冲突 | 0 |
| 跨学科映射 | 0 |
| 缺失目标 code | 0 |
| 非启用或非三级目标节点 | 0 |
| 当前迁移备份记录 | 0 |
| 是否需要逐条人工处理 | 否 |

**Dry Run 结论：通过。**

当前 18 条记录都可以通过已确认的题目旧标签和 Revision C primary 关联链，唯一解析到启用的 v1.1 三级知识点。当前数据中不存在同一用户的多条旧状态汇入同一目标节点，因此 Revision D 不需要执行数值合并。

## 二、当前全部 knowledge_status 记录及映射预览

| id | user_id | subject | 旧 knowledge_point | attempt | correct | ai_gap | mastery | last_practiced_at（北京时间） | new_knowledge_point_code | 标准名称 | 依据 | 结果 |
|---:|---:|---|---|---:|---:|---:|---:|---|---|---|---|---|
| 1 | 1 | 英语 | 动词辨析 | 1 | 1 | 0 | 100 | 2026-07-22 16:57:29.795696+08 | `ENG-VOCAB-COLLOCATION` | 固定搭配 | 题目 41 的 Revision C primary | safe |
| 2 | 1 | 英语 | 形容词辨析 | 1 | 1 | 0 | 100 | 2026-07-22 16:57:29.975332+08 | `ENG-VOCAB-CONTEXT-VERB` | 动词语境辨析 | 题目 42 的 Revision C primary；修正旧标签词性错误 | safe |
| 3 | 1 | 英语 | 现在完成时 | 1 | 1 | 0 | 100 | 2026-07-22 16:57:30.111101+08 | `ENG-GRAMMAR-TENSE-PRESENT-PERFECT` | 现在完成时 | 题目 44 的 Revision C primary | safe |
| 4 | 1 | 物理 | 位移与路程 | 1 | 1 | 0 | 100 | 2026-07-22 16:57:30.257359+08 | `PHY-MOTION-DISPLACEMENT-DISTANCE` | 位移与路程 | 题目 22 的 Revision C primary | safe |
| 5 | 1 | 物理 | 速度公式 | 1 | 1 | 0 | 100 | 2026-07-22 16:57:30.392916+08 | `PHY-KINEMATICS-UNIFORM-ACCELERATION` | 匀变速直线运动规律 | 题目 23 的 Revision C primary；应用 v1.1 redirect | safe |
| 6 | 1 | 数学 | 充分条件与必要条件 | 1 | 0 | 0 | 0 | 2026-07-22 16:57:30.401592+08 | `MATH-LOGIC-SUFFICIENT-NECESSARY` | 充分条件与必要条件 | 题目 2 的 Revision C primary | safe |
| 7 | 2 | 英语 | 动词辨析 | 1 | 1 | 0 | 100 | 2026-07-23 10:34:24.732058+08 | `ENG-VOCAB-COLLOCATION` | 固定搭配 | 题目 41 的 Revision C primary | safe |
| 8 | 2 | 英语 | 形容词辨析 | 1 | 1 | 0 | 100 | 2026-07-23 10:34:37.786495+08 | `ENG-VOCAB-CONTEXT-VERB` | 动词语境辨析 | 题目 42 的 Revision C primary；修正旧标签词性错误 | safe |
| 9 | 2 | 英语 | 现在完成时 | 1 | 0 | 0 | 0 | 2026-07-23 10:34:41.825355+08 | `ENG-GRAMMAR-TENSE-PRESENT-PERFECT` | 现在完成时 | 题目 44 的 Revision C primary | safe |
| 10 | 2 | 物理 | 位移与路程 | 1 | 1 | 0 | 100 | 2026-07-23 10:35:07.634285+08 | `PHY-MOTION-DISPLACEMENT-DISTANCE` | 位移与路程 | 题目 22 的 Revision C primary | safe |
| 11 | 2 | 物理 | 速度公式 | 1 | 1 | 0 | 100 | 2026-07-23 10:35:15.229727+08 | `PHY-KINEMATICS-UNIFORM-ACCELERATION` | 匀变速直线运动规律 | 题目 23 的 Revision C primary；应用 v1.1 redirect | safe |
| 12 | 2 | 数学 | 充分条件与必要条件 | 2 | 2 | 0 | 100 | 2026-07-23 11:24:42.908884+08 | `MATH-LOGIC-SUFFICIENT-NECESSARY` | 充分条件与必要条件 | 题目 2 的 Revision C primary | safe |
| 13 | 2 | 数学 | 集合的交集 | 1 | 1 | 0 | 100 | 2026-07-23 11:24:42.894978+08 | `MATH-SET-OPERATIONS` | 集合的基本运算 | 题目 1 的 Revision C primary；应用 v1.1 redirect | safe |
| 14 | 2 | 数学 | 一元二次不等式 | 1 | 1 | 0 | 100 | 2026-07-23 11:57:11.502631+08 | `MATH-INEQUALITY-QUADRATIC` | 一元二次不等式的解法 | 题目 13 的 Revision C primary | safe |
| 15 | 2 | 数学 | 函数定义域 | 1 | 1 | 0 | 100 | 2026-07-23 11:57:11.512254+08 | `MATH-FUNCTION-DOMAIN` | 函数的定义域 | 题目 3 的 Revision C primary | safe |
| 16 | 2 | 数学 | 函数单调性 | 1 | 1 | 0 | 100 | 2026-07-23 11:57:11.519461+08 | `MATH-FUNCTION-MONOTONICITY` | 函数的单调性 | 题目 4 的 Revision C primary | safe |
| 17 | 2 | 数学 | 函数奇偶性 | 1 | 1 | 0 | 100 | 2026-07-23 11:57:11.525675+08 | `MATH-FUNCTION-PARITY` | 函数的奇偶性 | 题目 5 的 Revision C primary | safe |
| 18 | 2 | 数学 | 对数运算 | 1 | 1 | 0 | 100 | 2026-07-23 11:57:11.532166+08 | `MATH-LOGARITHM-OPERATION` | 对数运算 | 题目 7 的 Revision C primary | safe |

当前所有记录的 `knowledge_point_id`、`mapping_version` 和 `mapped_at` 均为空；本报告只展示未来写入目标，不执行写入。

## 三、映射方法

本次使用以下只读解析顺序：

1. 使用 `knowledge_status.subject + knowledge_status.knowledge_point` 匹配当前题目的 `subject + questions.knowledge_points`。
2. 从匹配题目的 `question_knowledge_points` 读取 Revision C 的唯一 primary。
3. 校验目标 `knowledge_points` 记录存在、学科一致、`level=3` 且 `is_active=true`。
4. 对 v1 历史节点应用已批准的 `kp-mapping-v1.1` redirect，不把 redirected 或 ability-only 节点写入画像。

该方法避免仅依赖当前别名表。当前别名表中的“速度公式”和“集合的交集”仍指向 v1 历史节点，Revision D 必须使用 v1.1 最终目标：

| 旧 knowledge_point | 历史 code | Revision D 最终 code |
|---|---|---|
| 速度公式 | `PHY-KINEMATICS-VELOCITY-EQUATION` | `PHY-KINEMATICS-UNIFORM-ACCELERATION` |
| 集合的交集 | `MATH-SET-INTERSECTION` | `MATH-SET-OPERATIONS` |

## 四、潜在合并冲突

合并冲突定义为：同一 `user_id` 的两条或更多 `knowledge_status` 记录解析到相同的新 `knowledge_point_id`。

当前检查结果：

- 实际合并冲突：0 组。
- 需要合并的记录：0 条。
- 不需要决定 `attempt_count`、`correct_count`、`ai_gap_count`、`mastery_score` 或 `last_practiced_at` 的合并策略。

虽然用户 1 和用户 2 存在相同知识点状态，但它们属于不同用户，不构成冲突。

未来数据可能出现的典型合并包括：

- “动词辨析”与“介词搭配”同时归入 `ENG-VOCAB-COLLOCATION`。
- “关系代词 that”与“关系副词 where”同时归入 `ENG-CLAUSE-RELATIVE-WORD-SELECTION`。

正式 Revision D 仍应实现冲突预检并在遇到未定义合并时失败，而不能静默覆盖。

## 五、无法映射与人工处理

### 无法映射

无。18 条记录全部具备唯一目标。

### 是否需要人工处理

当前数据不需要逐条人工处理。正式迁移前仍需人工确认迁移规则本身：

- 只填写新增的 `knowledge_point_id`、`mapping_version`、`mapped_at`，保留旧 `subject` 和 `knowledge_point` 字段用于兼容。
- 在写入前创建 `knowledge_status_migration_backups` 快照。
- 如果正式执行时数据已发生变化，必须重新运行 Dry Run。
- 如果出现同一用户多条记录指向同一目标，应停止并提交合并方案，不应自动覆盖。

## 六、Revision D 执行前置条件

```text
Revision D data readiness: PASS
Safely mappable: 18
Unmappable: 0
Merge conflicts: 0
Manual execution authorization: PENDING
```

本报告仅用于人工审查，不代表已经执行 Revision D。
