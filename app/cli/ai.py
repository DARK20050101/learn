import argparse
import asyncio
import json
import sys
from time import perf_counter
from urllib.parse import urlparse

from fastapi import HTTPException

from app.config import settings
from app.schemas.ai_analysis import AIAnalysisInput
from app.services.llm import OpenAICompatibleLLMService


def _provider_name(base_url: str) -> str:
    hostname = (urlparse(base_url).hostname or "").lower()
    if "deepseek" in hostname:
        return "DeepSeek"
    if "openai" in hostname:
        return "OpenAI"
    return hostname or "OpenAI-compatible"


def configuration_report() -> dict[str, object]:
    return {
        "provider": _provider_name(settings.llm_base_url),
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "enabled": settings.llm_enabled,
        "api_key_configured": bool(settings.llm_api_key),
        "timeout_seconds": settings.llm_timeout_seconds,
        "max_retries": settings.llm_max_retries,
    }


async def connection_report() -> dict[str, object]:
    if not settings.llm_enabled:
        return {"passed": False, "error": "LLM_ENABLED=false"}
    if not settings.llm_api_key:
        return {"passed": False, "error": "LLM_API_KEY未配置"}

    data = AIAnalysisInput(
        question="函数 f(x)=2x+1 的单调性是什么？",
        student_answer="递减",
        correct_answer="递增",
        knowledge_points=["函数单调性"],
        standard_solution="一次函数斜率为正，因此单调递增。",
    )
    started = perf_counter()
    try:
        result = await OpenAICompatibleLLMService().analyze_mistake(data)
    except HTTPException as exc:
        return {
            "passed": False,
            "latency_ms": round((perf_counter() - started) * 1000),
            "error": str(exc.detail),
        }
    except Exception as exc:
        return {
            "passed": False,
            "latency_ms": round((perf_counter() - started) * 1000),
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "passed": True,
        "latency_ms": round((perf_counter() - started) * 1000),
        "json_output_valid": True,
        "mistake_type": result.mistake_type,
        "knowledge_gap": result.knowledge_gap,
    }


async def run_doctor(check_connection: bool) -> dict[str, object]:
    report: dict[str, object] = {
        "command": "ai doctor",
        "configuration": configuration_report(),
    }
    if check_connection:
        report["connection"] = await connection_report()
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai", description="AI服务配置与连通性诊断")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor", help="检查AI配置，不输出API Key")
    doctor.add_argument(
        "--check-connection",
        action="store_true",
        help="发送一次最小结构化错题分析请求",
    )
    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    report = asyncio.run(run_doctor(args.check_connection))
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    connection = report.get("connection")
    failed = isinstance(connection, dict) and not connection.get("passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
