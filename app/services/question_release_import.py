import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_point import KnowledgePoint, QuestionKnowledgePoint
from app.models.question import Question
from app.models.question_import import ImportStatus, QuestionImportBatch
from app.schemas.question_import import QuestionImportItem
from app.services.question_bank_quality import MAPPING_VERSION, _catalog, _resolve_code
from app.services.question_importer import (
    QuestionFileError,
    parse_question_json,
    question_fingerprint,
)

RELEASE_LOCK_KEY = "question-bank-release-import-v1"


class QuestionReleaseImportError(ValueError):
    """Raised when a release batch cannot be imported atomically."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__("题库发布导入失败")
        self.errors = errors


@dataclass(frozen=True)
class PreparedQuestion:
    index: int
    item: QuestionImportItem
    content_hash: str
    primary_code: str
    knowledge_point_id: int


def _validation_messages(exc: ValidationError) -> list[str]:
    messages = []
    for error in exc.errors(include_url=False):
        location = ".".join(str(part) for part in error["loc"])
        messages.append(f"{location}: {error['msg']}" if location else error["msg"])
    return messages


async def prepare_release(
    db: AsyncSession,
    *,
    filename: str,
    content: bytes,
    mapping_version: str = MAPPING_VERSION,
) -> tuple[list[PreparedQuestion], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if mapping_version != MAPPING_VERSION:
        return [], [
            {
                "index": 0,
                "question": None,
                "errors": [
                    f"mapping_version 必须为 {MAPPING_VERSION}，收到 {mapping_version}"
                ],
            }
        ]

    try:
        raw_items = parse_question_json(content)
    except QuestionFileError as exc:
        return [], [{"index": 0, "question": None, "errors": [str(exc)]}]

    catalog = await _catalog(db)
    prepared: list[PreparedQuestion] = []
    seen_hashes: dict[str, int] = {}
    for index, raw in enumerate(raw_items, start=1):
        try:
            item = QuestionImportItem.model_validate(raw)
        except ValidationError as exc:
            errors.append(
                {
                    "index": index,
                    "question": str(raw.get("question", ""))[:100] or None,
                    "errors": _validation_messages(exc),
                }
            )
            continue

        content_hash = question_fingerprint(item)
        if content_hash in seen_hashes:
            errors.append(
                {
                    "index": index,
                    "question": item.question[:100],
                    "errors": [f"与当前文件第 {seen_hashes[content_hash]} 题重复"],
                }
            )
            continue
        seen_hashes[content_hash] = index

        code, code_errors = _resolve_code(item, catalog)
        if code_errors or code is None:
            errors.append(
                {
                    "index": index,
                    "question": item.question[:100],
                    "errors": code_errors or ["知识点 code 无法解析"],
                }
            )
            continue
        knowledge_point = catalog["by_code"][code]
        prepared.append(
            PreparedQuestion(
                index=index,
                item=item,
                content_hash=content_hash,
                primary_code=code,
                knowledge_point_id=knowledge_point.id,
            )
        )

    if errors:
        return [], errors
    if len(prepared) != len(raw_items):
        return [], [
            {
                "index": 0,
                "question": None,
                "errors": [f"{filename} 未能完整解析全部题目"],
            }
        ]
    return prepared, []


async def _existing_primary_codes(
    db: AsyncSession,
    hashes: list[str],
) -> dict[str, tuple[int, str | None]]:
    if not hashes:
        return {}
    rows = (
        await db.execute(
            select(Question.id, Question.content_hash, KnowledgePoint.code)
            .outerjoin(
                QuestionKnowledgePoint,
                (QuestionKnowledgePoint.question_id == Question.id)
                & (QuestionKnowledgePoint.role == "primary"),
            )
            .outerjoin(
                KnowledgePoint,
                KnowledgePoint.id == QuestionKnowledgePoint.knowledge_point_id,
            )
            .where(Question.content_hash.in_(hashes))
        )
    ).all()
    return {
        row.content_hash: (row.id, row.code)
        for row in rows
        if row.content_hash is not None
    }


async def pre_import_report(
    db: AsyncSession,
    *,
    path: Path,
    mapping_version: str = MAPPING_VERSION,
) -> dict[str, Any]:
    content = path.read_bytes()
    prepared, errors = await prepare_release(
        db,
        filename=path.name,
        content=content,
        mapping_version=mapping_version,
    )
    existing = await _existing_primary_codes(
        db,
        [item.content_hash for item in prepared],
    )
    conflicts = []
    matching_duplicates = 0
    for item in prepared:
        current = existing.get(item.content_hash)
        if current is None:
            continue
        if current[1] == item.primary_code:
            matching_duplicates += 1
        else:
            conflicts.append(
                {
                    "index": item.index,
                    "question_id": current[0],
                    "expected_code": item.primary_code,
                    "actual_code": current[1],
                    "error": "已存在题目的 primary 关联缺失或冲突",
                }
            )

    state = await database_state(db)
    all_errors = [*errors, *conflicts]
    return {
        "report": "pre_import",
        "filename": path.name,
        "file_hash": hashlib.sha256(content).hexdigest(),
        "mapping_version": mapping_version,
        "database": state,
        "total": len(prepared) if not errors else 0,
        "new_questions": len(prepared) - len(existing),
        "matching_duplicates": matching_duplicates,
        "conflicts": len(conflicts),
        "errors": all_errors,
        "ready": not all_errors,
        "items": [
            {
                "index": item.index,
                "content_hash": item.content_hash,
                "primary_code": item.primary_code,
                "status": "existing" if item.content_hash in existing else "new",
            }
            for item in prepared
        ],
    }


async def _record_failed_batch(
    db: AsyncSession,
    *,
    filename: str,
    content: bytes,
    total_count: int,
    errors: list[dict[str, Any]],
) -> int:
    batch = QuestionImportBatch(
        filename=Path(filename).name,
        file_hash=hashlib.sha256(content).hexdigest(),
        total_count=total_count,
        imported_count=0,
        duplicate_count=0,
        failed_count=total_count,
        status=ImportStatus.failed,
        errors=errors,
    )
    db.add(batch)
    await db.commit()
    return batch.id


async def import_release(
    db: AsyncSession,
    *,
    filename: str,
    content: bytes,
    mapping_version: str = MAPPING_VERSION,
) -> dict[str, Any]:
    try:
        raw_count = len(parse_question_json(content))
    except QuestionFileError:
        raw_count = 1

    await db.rollback()
    try:
        async with db.begin():
            await db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": RELEASE_LOCK_KEY},
            )
            prepared, errors = await prepare_release(
                db,
                filename=filename,
                content=content,
                mapping_version=mapping_version,
            )
            if errors:
                raise QuestionReleaseImportError(errors)

            existing = await _existing_primary_codes(
                db,
                [item.content_hash for item in prepared],
            )
            conflicts = []
            for item in prepared:
                current = existing.get(item.content_hash)
                if current is not None and current[1] != item.primary_code:
                    conflicts.append(
                        {
                            "index": item.index,
                            "question": item.item.question[:100],
                            "errors": [
                                "已存在题目的 primary 关联缺失或冲突："
                                f"expected={item.primary_code}, actual={current[1]}"
                            ],
                        }
                    )
            if conflicts:
                raise QuestionReleaseImportError(conflicts)

            batch = QuestionImportBatch(
                filename=Path(filename).name,
                file_hash=hashlib.sha256(content).hexdigest(),
                total_count=len(prepared),
                imported_count=0,
                duplicate_count=0,
                failed_count=0,
                status=ImportStatus.processing,
                errors=[],
            )
            db.add(batch)
            await db.flush()

            imported_ids: list[int] = []
            duplicate_ids: list[int] = []
            for item in prepared:
                current = existing.get(item.content_hash)
                if current is not None:
                    duplicate_ids.append(current[0])
                    continue
                question = Question(**item.item.as_question_values(item.content_hash))
                db.add(question)
                await db.flush()
                db.add(
                    QuestionKnowledgePoint(
                        question_id=question.id,
                        knowledge_point_id=item.knowledge_point_id,
                        role="primary",
                        weight=1.0,
                        source="release_import",
                        mapping_version=mapping_version,
                    )
                )
                imported_ids.append(question.id)

            batch.imported_count = len(imported_ids)
            batch.duplicate_count = len(duplicate_ids)
            batch.status = ImportStatus.completed
            await db.flush()
            batch_id = batch.id
    except QuestionReleaseImportError as exc:
        await db.rollback()
        failed_batch_id = await _record_failed_batch(
            db,
            filename=filename,
            content=content,
            total_count=raw_count,
            errors=exc.errors,
        )
        exc.errors.append({"batch_id": failed_batch_id})
        raise
    except Exception as exc:
        await db.rollback()
        failure_errors = [
            {
                "index": 0,
                "question": None,
                "errors": [f"事务执行失败：{type(exc).__name__}: {exc}"],
            }
        ]
        failed_batch_id = await _record_failed_batch(
            db,
            filename=filename,
            content=content,
            total_count=raw_count,
            errors=failure_errors,
        )
        failure_errors.append({"batch_id": failed_batch_id})
        raise QuestionReleaseImportError(failure_errors) from exc

    return {
        "batch_id": batch_id,
        "filename": Path(filename).name,
        "status": ImportStatus.completed.value,
        "total_count": len(prepared),
        "imported_count": len(imported_ids),
        "duplicate_count": len(duplicate_ids),
        "failed_count": 0,
        "imported_question_ids": imported_ids,
        "duplicate_question_ids": duplicate_ids,
        "mapping_version": mapping_version,
    }


def _question_business_hash(rows: list[Any]) -> str:
    serialized = []
    for row in rows:
        serialized.append(
            {
                "id": row.id,
                "title": row.title,
                "content": row.content,
                "subject": row.subject,
                "chapter": row.chapter,
                "question_type": row.question_type.value,
                "options": row.options,
                "correct_answer": row.correct_answer,
                "explanation": row.explanation,
                "source": row.source,
                "content_hash": row.content_hash,
                "difficulty": row.difficulty,
                "knowledge_points": row.knowledge_points,
                "tags": row.tags,
                "is_active": row.is_active,
            }
        )
    payload = json.dumps(
        serialized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def database_state(
    db: AsyncSession,
    *,
    question_ids: list[int] | None = None,
) -> dict[str, Any]:
    question_count = await db.scalar(select(func.count()).select_from(Question))
    primary_count = await db.scalar(
        select(func.count())
        .select_from(QuestionKnowledgePoint)
        .where(QuestionKnowledgePoint.role == "primary")
    )
    orphan_count = await db.scalar(
        select(func.count())
        .select_from(Question)
        .outerjoin(
            QuestionKnowledgePoint,
            (QuestionKnowledgePoint.question_id == Question.id)
            & (QuestionKnowledgePoint.role == "primary"),
        )
        .where(QuestionKnowledgePoint.id.is_(None))
    )
    statement = select(Question).order_by(Question.id)
    if question_ids is not None:
        statement = statement.where(Question.id.in_(question_ids))
    rows = list((await db.execute(statement)).scalars())
    return {
        "questions": question_count,
        "primary_knowledge_point_links": primary_count,
        "orphan_questions": orphan_count,
        "selected_question_count": len(rows),
        "selected_questions_business_hash": _question_business_hash(rows),
    }


async def post_import_report(
    db: AsyncSession,
    *,
    path: Path,
    import_result: dict[str, Any],
    original_question_ids: list[int],
    original_questions_hash: str,
) -> dict[str, Any]:
    state = await database_state(db)
    original_state = await database_state(db, question_ids=original_question_ids)
    imported_ids = import_result["imported_question_ids"]
    new_state = await database_state(db, question_ids=imported_ids)
    expected_total = len(original_question_ids) + import_result["imported_count"]
    checks = {
        "question_count_expected": state["questions"] == expected_total,
        "primary_count_matches_questions": (
            state["primary_knowledge_point_links"] == state["questions"]
        ),
        "no_orphan_questions": state["orphan_questions"] == 0,
        "new_questions_have_primary": (
            new_state["selected_question_count"] == len(imported_ids)
            and len(imported_ids) == import_result["imported_count"]
        ),
        "original_questions_unchanged": (
            original_state["selected_question_count"] == len(original_question_ids)
            and original_state["selected_questions_business_hash"]
            == original_questions_hash
        ),
    }
    return {
        "report": "post_import",
        "filename": path.name,
        "mapping_version": import_result["mapping_version"],
        "import_result": import_result,
        "database": state,
        "original_questions": original_state,
        "new_questions": new_state,
        "checks": checks,
        "passed": all(checks.values()),
        "recovery": {
            "strategy": (
                "restore_pre_import_pg_dump; or, only when imported questions have no "
                "dependent records, remove their links and questions in one audited transaction"
            ),
            "batch_id": import_result["batch_id"],
            "warning": "deleting the import batch record alone does not restore question data",
        },
    }
