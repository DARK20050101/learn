import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.question import Question
from app.services.question_bank_quality import MAPPING_VERSION
from app.services.question_release_import import (
    QuestionReleaseImportError,
    database_state,
    import_release,
    post_import_report,
    pre_import_report,
)


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


async def run(
    path: Path,
    *,
    dry_run: bool,
    report_dir: Path,
    mapping_version: str,
) -> int:
    stem = path.stem
    pre_path = report_dir / f"{stem}_pre_import_report.json"
    post_path = report_dir / f"{stem}_post_import_report.json"
    failure_path = report_dir / f"{stem}_failed_import_report.json"

    async with AsyncSessionLocal() as db:
        pre = await pre_import_report(
            db,
            path=path,
            mapping_version=mapping_version,
        )
        _write_report(pre_path, pre)
        print(json.dumps({"pre_report": str(pre_path), **pre}, ensure_ascii=False, indent=2))
        if not pre["ready"]:
            return 1
        if dry_run:
            return 0

        original_ids = list(
            (
                await db.execute(select(Question.id).order_by(Question.id))
            ).scalars()
        )
        original_state = await database_state(db, question_ids=original_ids)
        await db.rollback()
        try:
            result = await import_release(
                db,
                filename=path.name,
                content=path.read_bytes(),
                mapping_version=mapping_version,
            )
        except QuestionReleaseImportError as exc:
            failure = {
                "report": "failed_import",
                "filename": path.name,
                "mapping_version": mapping_version,
                "errors": exc.errors,
                "database": await database_state(db),
                "rollback": "completed",
            }
            _write_report(failure_path, failure)
            print(json.dumps(failure, ensure_ascii=False, indent=2))
            return 1

        post = await post_import_report(
            db,
            path=path,
            import_result=result,
            original_question_ids=original_ids,
            original_questions_hash=original_state["selected_questions_business_hash"],
        )
        _write_report(post_path, post)
        print(json.dumps({"post_report": str(post_path), **post}, ensure_ascii=False, indent=2))
        return 0 if post["passed"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="事务化导入审核题库并创建标准 primary 知识点关联"
    )
    parser.add_argument("file", type=Path, help="待发布的 JSON 题库文件")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只生成导入前报告，不写数据库和导入批次",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("data/question_bank/reports"),
        help="导入前后验证报告目录",
    )
    parser.add_argument(
        "--mapping-version",
        default=MAPPING_VERSION,
        help=f"固定映射版本，当前必须为 {MAPPING_VERSION}",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(
        asyncio.run(
            run(
                args.file,
                dry_run=args.dry_run,
                report_dir=args.report_dir,
                mapping_version=args.mapping_version,
            )
        )
    )


if __name__ == "__main__":
    main()
