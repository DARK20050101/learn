from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.database import AsyncSessionLocal, engine
from app.models.question import Question
from app.schemas.question_import import QuestionImportItem
from app.services.question_importer import question_fingerprint

REVISE_ITEMS = {2, 13, 17, 18, 23, 24, 31, 34, 35, 39, 43, 46, 47}
DIFFICULTIES = {
    1: 3, 2: 3, 3: 2, 4: 2, 5: 2, 6: 3, 7: 2, 8: 4, 9: 2, 10: 3,
    11: 2, 12: 2, 13: 2, 14: 2, 15: 2, 16: 2, 17: 3, 18: 3, 19: 3, 20: 3,
    21: 4, 22: 3, 23: 4, 24: 4, 25: 3, 26: 3, 27: 2, 28: 4, 29: 3, 30: 3,
    31: 3, 32: 2, 33: 4, 34: 4, 35: 2, 36: 2, 37: 2, 38: 2, 39: 2, 40: 2,
    41: 2, 42: 2, 43: 1, 44: 2, 45: 2, 46: 2, 47: 2, 48: 2, 49: 2, 50: 1,
}


def reviewed_tags(tags: list[str], passed: bool) -> list[str]:
    result = [
        tag for tag in tags
        if tag not in {"review:required", "review:passed", "review:revise"}
    ]
    result.append("review:passed" if passed else "review:revise")
    return result


def load_manifest(path: Path) -> list[dict[str, Any]]:
    questions = json.loads(path.read_text(encoding="utf-8"))["questions"]
    if len(questions) != 50 or set(DIFFICULTIES) != set(range(1, 51)):
        raise ValueError("审核清单必须完整覆盖50题")
    return [
        {
            **question,
            "content_hash": question_fingerprint(
                QuestionImportItem.model_validate(question)
            ),
        }
        for question in questions
    ]


async def apply_review(manifest: Path, dry_run: bool) -> dict[str, Any]:
    items = load_manifest(manifest)
    hashes = [item["content_hash"] for item in items]
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.scalars(
                select(Question)
                .where(Question.content_hash.in_(hashes))
                .with_for_update()
            )
            questions = {question.content_hash: question for question in result}
            missing = [value for value in hashes if value not in questions]
            if missing:
                raise RuntimeError(f"数据库缺少审核目标题目: {missing}")

            rows: list[dict[str, Any]] = []
            for number, item in enumerate(items, 1):
                question = questions[item["content_hash"]]
                passed = number not in REVISE_ITEMS
                before = {
                    "difficulty": question.difficulty,
                    "is_active": question.is_active,
                    "tags": list(question.tags),
                }
                after = {
                    "difficulty": DIFFICULTIES[number],
                    "is_active": passed,
                    "tags": reviewed_tags(list(question.tags), passed),
                }
                rows.append({
                    "number": number,
                    "question_id": question.id,
                    "decision": "PASS" if passed else "REVISE",
                    "before": before,
                    "after": after,
                })
                if not dry_run:
                    question.difficulty = after["difficulty"]
                    question.is_active = after["is_active"]
                    question.tags = after["tags"]
            if dry_run:
                await session.rollback()

    return {
        "dry_run": dry_run,
        "total": len(rows),
        "pass": sum(row["decision"] == "PASS" for row in rows),
        "revise": sum(row["decision"] == "REVISE" for row in rows),
        "active_after": sum(row["after"]["is_active"] for row in rows),
        "inactive_after": sum(not row["after"]["is_active"] for row in rows),
        "items": rows,
    }


async def async_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/question_bank/reports/gaokao_bench_batch01_review_apply.json"),
    )
    args = parser.parse_args()
    report = await apply_review(args.manifest.resolve(), args.dry_run)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        key: report[key]
        for key in ("dry_run", "total", "pass", "revise", "active_after", "inactive_after")
    }, ensure_ascii=False, indent=2))
    print(f"report={args.report}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(async_main())
