import asyncio
import json
from typing import Protocol

import httpx
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.ai_analysis import AIAnalysisInput, AIAnalysisResult


class LLMService(Protocol):
    async def analyze_mistake(self, data: AIAnalysisInput) -> AIAnalysisResult: ...


class OpenAICompatibleLLMService:
    """The only infrastructure boundary that calls an external LLM API."""

    def __init__(self) -> None:
        self.url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"

    async def analyze_mistake(self, data: AIAnalysisInput) -> AIAnalysisResult:
        if not settings.llm_enabled or not settings.llm_api_key:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AI 分析服务尚未配置")
        prompt = {
            "题目": data.question,
            "学生答案": data.student_answer,
            "正确答案": data.correct_answer,
            "候选知识点": data.knowledge_points,
            "标准解析": data.standard_solution,
        }
        payload = {
            "model": settings.llm_model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是面向中国准高三学生的学习分析助手。只分析给定材料，"
                        "不重新判题，不修改标准答案，不虚构背景，不使用聊天式开场。"
                        "knowledge_gap 必须从候选知识点中选择。用简洁中文返回 JSON，"
                        "字段必须为 mistake_type、reason、knowledge_gap、suggestion、"
                        "next_training。mistake_type 只能是：概念理解错误、计算错误、"
                        "审题错误、方法选择错误、知识记忆错误、其他。建议必须具体可执行。"
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            for attempt in range(settings.llm_max_retries + 1):
                try:
                    response = await client.post(self.url, headers=headers, json=payload)
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                    return AIAnalysisResult.model_validate_json(content)
                except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
                    last_error = exc
                    if attempt < settings.llm_max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI 分析服务暂时不可用") from last_error


llm_service: LLMService = OpenAICompatibleLLMService()
