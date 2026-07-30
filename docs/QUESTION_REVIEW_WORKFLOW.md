# 题库高效审查与发布流程

## 目标

人工只处理机器无法可靠判断的问题。审批结果、修订内容、验证报告和发布批次全部保存在项目内，不通过下载文件人工传递。

## 标准流程

1. 自动审查把安全题写入 `data/question_bank/candidates/`。
2. 安全题通过事务发布命令直接导入。
3. 风险题写入 `data/question_bank/review_queue/`。
4. 审查页面自动发现队列，并把结论实时保存到 `data/question_bank/review_results/`。
5. `PASS` 题保持原内容；`REJECT` 题排除；`REVISE` 题必须在修订清单中提供明确修改。
6. `scripts/process_question_reviews.py` 合并队列、审批结果和修订清单，生成新的发布候选及处理报告。
7. 候选依次通过 lint、自动风险复检、数据库 dry-run。
8. 全部通过后使用事务发布；失败自动回滚并保留报告。

## 职责

- 人工审核：指出问题，或对机器风险给出明确覆盖决定。
- AI/Codex：根据备注修订题目、独立核对答案、生成修订清单并执行验证。
- 系统：阻止未审批、未修订、知识点不存在、重复或冲突题目进入发布候选。

## 手工修改方式

通常不需要直接改题目 JSON。若确实需要人工指定文本，只修改对应修订清单：

```text
data/question_bank/revisions/<batch>_revisions.json
```

以题目的稳定 `source` 为键，在 `updates` 中填写要替换的字段。`source`、`title`、`subject`、`chapter` 和 `knowledge_points` 是受保护字段，不能通过修订清单静默改变。

## 失败关闭

以下情况不会生成可发布候选：

- 存在未审批题目；
- `REVISE` 没有对应修订；
- 修订试图改变受保护字段；
- 修订清单包含队列中不存在的题目；
- lint、知识点校验或数据库 dry-run 失败。

人工 `PASS` 可以覆盖已知的展示风险，但覆盖决定会保留在审查结果和处理报告中，便于追踪。
