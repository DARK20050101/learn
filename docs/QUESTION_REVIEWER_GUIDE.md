# 题库审查工具使用指南

## 用途

该工具用于在题目进入正式数据库前进行人工教研审核。它独立于学生端和数据库，可以
重复用于未来任意批次，不会触发每日任务推荐。

## 启动

在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_question_reviewer.ps1
```

浏览器打开：

```text
http://127.0.0.1:5174/reviewer.html
```

## 载入题目

点击“选择 JSON 文件”，可一次选择一个或多个文件。支持：

- `{"questions": [...]}` 格式；
- 顶层题目数组格式。

推荐先选择：

- `data/question_bank/drafts/qinghai_six_subject_history_batch01_v1.json`
- `data/question_bank/drafts/qinghai_six_subject_history_batch02_v1.json`

文件只在浏览器本地读取，不会上传，也不会写入数据库。

## 审核流程

1. 默认隐藏答案，先独立作答。
2. 检查题干、选项、公式和图片依赖。
3. 点击“查看答案与解析”。
4. 核对答案唯一性和解析质量。
5. 检查知识点及难度。
6. 选择：
   - `PASS`：可以进入最终候选库；
   - `REVISE`：修改后重新审核；
   - `REJECT`：不进入题库。
7. 在备注中记录问题和修改建议。

审核记录按“文件名+文件内容哈希”隔离并自动保存到浏览器 `localStorage`。同一批文件
重新载入时会恢复进度；文件内容改变后会视为新批次，避免把旧结论错误套用到新题。

## 导出

点击“导出结果”生成：

```text
question_review_<batch_id>.json
```

导出文件包含批次标识、统计和逐题结论，可用于生成修订批次或正式发布清单。

## 限制

- 浏览器本地数据不是长期备份，应定期导出结果。
- 自动渲染仅处理 `$...$` 行内 LaTeX；复杂表格、图片及异常OCR仍需对照原卷。
- 审核工具不会自动修改题目，也不会导入数据库。
