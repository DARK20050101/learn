# AI 错题分析接入

系统把外部模型调用集中在 `app/services/llm.py`。路由、答题服务和前端都不直接持有 API Key，也不允许前端提交正确答案、知识点或提示词。

## 调用流程

1. 学生提交答案，后端根据数据库中的标准答案判题。
2. 正确题返回标准解析，`analysis_status=not_requested`，不调用模型。
3. 错题先保存答题记录，`analysis_status=pending`，随后启动后台分析。
4. 后端根据 `answer_id` 查询题目、学生答案、标准答案、标准解析和知识点。
5. 模型返回结构化 JSON，校验通过后保存到 `student_answers.ai_analysis`。
6. 调用失败或结构错误时标记为 `failed`，不影响判题、错题本和标准解析。
7. 学生可以在答题页对失败记录执行一次受控重试；正在处理或已经完成的记录不会重复调度。

## 本地配置

### DeepSeek 快速配置

在项目根目录运行：

~~~powershell
Set-Location E:\1a
.\configure_ai.ps1
~~~

脚本会把 DeepSeek 配置写入已被 Git 忽略的本地 `.env`，并执行一次最小连接测试。API Key 不会显示在诊断结果中，也不会写入前端。如果暂时只想保存配置、不访问外部服务，可以运行：

~~~powershell
.\configure_ai.ps1 -SkipConnectionCheck
~~~

不修改配置时，也可单独检查当前状态：

~~~powershell
.\.venv\Scripts\python.exe -m app.cli.ai doctor
.\.venv\Scripts\python.exe -m app.cli.ai doctor --check-connection
~~~

DeepSeek 当前配置使用 `https://api.deepseek.com` 和 `deepseek-v4-flash`。修改 `.env` 后需要重启 FastAPI 服务。

### 手动配置

复制 `.env.example` 为 `.env`，填写兼容 OpenAI Chat Completions 协议的服务：

```env
LLM_ENABLED=true
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4.1-mini
LLM_TIMEOUT_SECONDS=20
LLM_MAX_RETRIES=2
```

`LLM_BASE_URL` 不要包含 `/chat/completions`，服务会自动拼接该路径。API Key 只保存在后端环境变量中，不要写入前端、Git或题库JSON。

使用其他兼容服务时，只需要替换 `LLM_BASE_URL`、`LLM_API_KEY` 和 `LLM_MODEL`。如果供应商不兼容 `response_format={"type":"json_object"}`，应在 `app/services/llm.py` 内新增单独适配器，不能把供应商调用散落到路由中。

## 输出契约

模型必须返回：

```json
{
  "mistake_type": "概念理解错误",
  "reason": "学生混淆了定义域限制与函数值计算。",
  "knowledge_gap": "函数的定义域",
  "suggestion": "先标出根式和分母带来的限制，再求交集。",
  "next_training": "完成2道含根式和分式的定义域题。"
}
```

`knowledge_gap` 必须属于该题已有知识点；模型返回未知名称时，后端会回退到题目主知识点。

## 验证

配置并启动服务后：

1. 提交一道正确题，确认网络日志中没有模型请求。
2. 提交一道错误题，确认接口先返回 `pending`。
3. 轮询 `GET /api/v1/student-answers/{answer_id}/analysis`，最终应为 `completed`。
4. 临时填入无效Key，确认答题仍正常保存且状态变为 `failed`。
5. 恢复Key后调用 `POST /api/v1/student-answers/{answer_id}/analysis/retry`，确认分析可以完成。

生产环境还应设置供应商侧预算、速率限制和用量告警。
