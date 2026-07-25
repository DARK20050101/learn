import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.question_import import ImportStatus, QuestionImportBatch
from app.schemas.question_import import (
    ImportErrorDetail,
    QuestionImportItem,
    QuestionImportResult,
)


class QuestionFileError(ValueError):
    """Raised when an import file cannot be decoded into question objects."""


def parse_question_json(content: bytes) -> list[dict[str, Any]]:
    try:
        payload = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QuestionFileError(f"JSON 文件无法解析：{exc}") from exc
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict) and "questions" in payload:
        items = payload["questions"]
    elif isinstance(payload, dict):
        items = [payload]
    else:
        raise QuestionFileError("JSON 根节点必须是题目对象、题目数组或包含 questions 的对象")
    if not isinstance(items, list):
        raise QuestionFileError("questions 必须是数组")
    if not items:
        raise QuestionFileError("题库文件不能为空")
    if any(not isinstance(item, dict) for item in items):
        raise QuestionFileError("题目数组中的每一项都必须是对象")
    return items


def question_fingerprint(item: QuestionImportItem) -> str:
    canonical = {
        "subject": item.subject.strip().casefold(),
        "chapter": item.chapter.strip().casefold(),
        "type": item.type.value,
        "question": " ".join(item.question.split()).casefold(),
        "options": [" ".join(option.split()).casefold() for option in item.options],
        "answer": item.answer,
    }
    serialized = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _validation_messages(exc: ValidationError) -> list[str]:
    messages = []
    for error in exc.errors(include_url=False):
        location = ".".join(str(part) for part in error["loc"])
        messages.append(f"{location}: {error['msg']}" if location else error["msg"])
    return messages


async def import_questions(
    db: AsyncSession, *, filename: str, content: bytes
) -> QuestionImportResult:
    batch = QuestionImportBatch(
        filename=Path(filename).name,
        file_hash=hashlib.sha256(content).hexdigest(),
        total_count=0,
        status=ImportStatus.processing,
        errors=[],
    )
    db.add(batch)
    await db.flush()
    try:
        raw_items = parse_question_json(content)
    except QuestionFileError as exc:
        detail = ImportErrorDetail(index=0, errors=[str(exc)])
        batch.status = ImportStatus.failed
        batch.failed_count = 1
        batch.errors = [detail.model_dump()]
        await db.commit()
        raise
    batch.total_count = len(raw_items)

    errors: list[ImportErrorDetail] = []
    seen_hashes: set[str] = set()
    imported_count = 0
    duplicate_count = 0

    for index, raw in enumerate(raw_items, start=1):
        try:
            item = QuestionImportItem.model_validate(raw)
        except ValidationError as exc:
            errors.append(
                ImportErrorDetail(
                    index=index,
                    question=str(raw.get("question", ""))[:100] or None,
                    errors=_validation_messages(exc),
                )
            )
            continue

        content_hash = question_fingerprint(item)
        if content_hash in seen_hashes:
            duplicate_count += 1
            errors.append(
                ImportErrorDetail(
                    index=index,
                    question=item.question[:100],
                    errors=["与当前文件中的其他题目重复"],
                )
            )
            continue
        seen_hashes.add(content_hash)

        statement = (
            insert(Question)
            .values(**item.as_question_values(content_hash))
            .on_conflict_do_nothing(index_elements=[Question.content_hash])
        )
        result = await db.execute(statement)
        if result.rowcount == 0:
            duplicate_count += 1
            errors.append(
                ImportErrorDetail(
                    index=index,
                    question=item.question[:100],
                    errors=["数据库中已存在相同题目"],
                )
            )
        else:
            imported_count += 1

    failed_count = len(raw_items) - imported_count - duplicate_count
    batch.imported_count = imported_count
    batch.duplicate_count = duplicate_count
    batch.failed_count = failed_count
    batch.errors = [error.model_dump() for error in errors]
    batch.status = ImportStatus.completed if not errors else ImportStatus.completed_with_errors
    await db.commit()

    return QuestionImportResult(
        batch_id=batch.id,
        filename=batch.filename,
        status=batch.status,
        total_count=batch.total_count,
        imported_count=imported_count,
        duplicate_count=duplicate_count,
        failed_count=failed_count,
        errors=errors,
    )
