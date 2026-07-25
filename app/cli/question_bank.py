import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from app.database import AsyncSessionLocal
from app.services.question_bank_quality import (
    coverage_report,
    difficulty_report,
    lint_file,
    missing_report,
    render_markdown,
    verify_database,
    verify_files,
)


def _write_report(report: dict[str, Any], output: Path | None) -> None:
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    print(serialized)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() == ".md":
            output.write_text(render_markdown(report), encoding="utf-8")
        else:
            output.write_text(serialized + "\n", encoding="utf-8")


async def _run_database_command(args: argparse.Namespace) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        if args.command == "coverage":
            return await coverage_report(db, subject=args.subject)
        if args.command == "difficulty":
            return await difficulty_report(db, subject=args.subject)
        if args.command == "missing":
            return await missing_report(
                db,
                subject=args.subject,
                minimum=args.minimum,
            )
        if args.files:
            return await verify_files(db, args.files)
        return await verify_database(db)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="question_bank",
        description="只读题库质量检查与统计工具",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint = subparsers.add_parser("lint", help="检查 JSON 文件格式与基础质量")
    lint.add_argument("files", nargs="+", type=Path)
    lint.add_argument("--report", type=Path, help="输出 JSON 或 Markdown 报告")

    for command, help_text in (
        ("coverage", "输出标准知识点覆盖统计"),
        ("difficulty", "输出题目难度分布"),
        ("missing", "输出题量不足的标准知识点"),
    ):
        child = subparsers.add_parser(command, help=help_text)
        child.add_argument("--subject", choices=["数学", "物理", "英语"])
        child.add_argument("--report", type=Path, help="输出 JSON 或 Markdown 报告")
        if command == "missing":
            child.add_argument("--minimum", type=int, default=5)

    verify = subparsers.add_parser(
        "verify",
        help="检查正式题库，或对 JSON 执行数据库感知的导入前预检查",
    )
    verify.add_argument("files", nargs="*", type=Path)
    verify.add_argument("--report", type=Path, help="输出 JSON 或 Markdown 报告")
    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    if args.command == "lint":
        reports = [lint_file(path) for path in args.files]
        report: dict[str, Any] = {
            "command": "lint",
            "total": sum(item["total"] for item in reports),
            "passed": sum(item["passed"] for item in reports),
            "errors": sum(item["errors"] for item in reports),
            "warnings": sum(item["warnings"] for item in reports),
            "files": reports,
        }
    else:
        if args.command == "missing" and args.minimum < 1:
            raise SystemExit("--minimum 必须大于 0")
        report = asyncio.run(_run_database_command(args))
    _write_report(report, args.report)
    raise SystemExit(1 if report.get("errors", 0) else 0)


if __name__ == "__main__":
    main()
