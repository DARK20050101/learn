from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.database import AsyncSessionLocal, engine
from app.models.knowledge_point import KnowledgePoint, QuestionKnowledgePoint
from app.models.question import Question
from app.schemas.question_import import QuestionImportItem
from app.services.question_importer import question_fingerprint


def load(path: Path) -> list[QuestionImportItem]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        QuestionImportItem.model_validate(item)
        for item in payload["questions"]
    ]


def primary_code(item: QuestionImportItem) -> str:
    codes = [tag[3:] for tag in item.tags if tag.startswith("kp:")]
    if len(codes) != 1:
        raise ValueError(f"{item.title} 必须包含一个kp标签")
    return codes[0]


async def apply(old_path: Path, new_path: Path, dry_run: bool) -> dict[str, Any]:
    old_payload = json.loads(old_path.read_text(encoding="utf-8"))["questions"]
    new_payload = json.loads(new_path.read_text(encoding="utf-8"))["questions"]
    if [item["answer"] for item in old_payload] != [
        item["answer"] for item in new_payload
    ]:
        raise ValueError("修订版不得修改标准答案")
    old_items = load(old_path)
    new_items = load(new_path)
    if len(old_items) != 50 or len(new_items) != 50:
        raise ValueError("v1和v2必须各包含50题")

    old_hashes = [question_fingerprint(item) for item in old_items]
    new_hashes = [question_fingerprint(item) for item in new_items]
    target_codes = {primary_code(item) for item in new_items}
    async with AsyncSessionLocal() as session:
        async with session.begin():
            questions_result = await session.scalars(
                select(Question)
                .where(Question.content_hash.in_(old_hashes))
                .with_for_update()
            )
            questions = {
                question.content_hash: question for question in questions_result
            }
            if set(questions) != set(old_hashes):
                raise RuntimeError("数据库题目与v1固定清单不一致")

            points_result = await session.scalars(
                select(KnowledgePoint).where(KnowledgePoint.code.in_(target_codes))
            )
            points = {point.code: point for point in points_result}
            if set(points) != target_codes:
                raise RuntimeError(
                    f"缺少知识点: {sorted(target_codes - set(points))}"
                )
            invalid = [
                point.code for point in points.values()
                if point.level != 3 or not point.is_active
            ]
            if invalid:
                raise RuntimeError(f"知识点不能作为primary: {invalid}")

            rows = []
            for number, (_old_item, new_item, old_hash, new_hash) in enumerate(
                zip(old_items, new_items, old_hashes, new_hashes, strict=True),
                1,
            ):
                question = questions[old_hash]
                link = await session.scalar(
                    select(QuestionKnowledgePoint)
                    .where(
                        QuestionKnowledgePoint.question_id == question.id,
                        QuestionKnowledgePoint.role == "primary",
                    )
                    .with_for_update()
                )
                if link is None:
                    raise RuntimeError(f"题目{question.id}缺少primary关联")
                code = primary_code(new_item)
                before = {
                    "content_hash": question.content_hash,
                    "difficulty": question.difficulty,
                    "is_active": question.is_active,
                    "knowledge_point_id": link.knowledge_point_id,
                }
                values = new_item.as_question_values(new_hash)
                values["is_active"] = True
                after = {
                    "content_hash": new_hash,
                    "difficulty": values["difficulty"],
                    "is_active": True,
                    "knowledge_point_id": points[code].id,
                }
                rows.append({
                    "number": number,
                    "question_id": question.id,
                    "changed_content": old_hash != new_hash,
                    "primary_code": code,
                    "before": before,
                    "after": after,
                })
                if not dry_run:
                    for key, value in values.items():
                        setattr(question, key, value)
                    link.knowledge_point_id = points[code].id
                    link.source = "review"
                    link.mapping_version = "kp-mapping-v1.2"
            if dry_run:
                await session.rollback()

    return {
        "dry_run": dry_run,
        "total": len(rows),
        "content_changed": sum(row["changed_content"] for row in rows),
        "activated": len(rows),
        "answers_unchanged": True,
        "items": rows,
    }


async def async_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/question_bank/reports/gaokao_bench_batch01_v2_apply.json"),
    )
    args = parser.parse_args()
    report = await apply(args.old.resolve(), args.new.resolve(), args.dry_run)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        key: report[key]
        for key in ("dry_run", "total", "content_changed", "activated", "answers_unchanged")
    }, ensure_ascii=False, indent=2))
    print(f"report={args.report}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(async_main())
