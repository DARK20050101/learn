import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_point import KnowledgePoint, KnowledgePointAlias, QuestionKnowledgePoint
from app.models.question import Question
from app.schemas.question_import import QuestionImportItem
from app.services.question_importer import (
    QuestionFileError,
    parse_question_json,
    question_fingerprint,
)

MAPPING_VERSION = "kp-mapping-v1.1"
REDIRECTS = {
    "MATH-SET-INTERSECTION": "MATH-SET-OPERATIONS",
    "PHY-KINEMATICS-VELOCITY-EQUATION": "PHY-KINEMATICS-UNIFORM-ACCELERATION",
    "PHY-OPTICS-REFRACTION-PHENOMENON": "PHY-OPTICS-REFRACTION",
    "ENG-CLAUSE-RELATIVE-THAT": "ENG-CLAUSE-RELATIVE-WORD-SELECTION",
    "ENG-CLAUSE-RELATIVE-WHERE": "ENG-CLAUSE-RELATIVE-WORD-SELECTION",
    "ENG-GRAMMAR-MODAL-MUST": "ENG-GRAMMAR-MODAL-BASIC",
}
FORBIDDEN_CODES = {"ENG-WRITING-SENTENCE-EXPRESSION"}


def _validation_messages(exc: ValidationError) -> list[str]:
    messages = []
    for error in exc.errors(include_url=False):
        location = ".".join(str(part) for part in error["loc"])
        messages.append(f"{location}: {error['msg']}" if location else error["msg"])
    return messages


def lint_content(content: bytes, *, filename: str) -> dict[str, Any]:
    report: dict[str, Any] = {
        "command": "lint",
        "schema_version": "question-bank-report-v1",
        "filename": filename,
        "total": 0,
        "passed": 0,
        "errors": 0,
        "warnings": 0,
        "items": [],
    }
    try:
        raw_items = parse_question_json(content)
    except QuestionFileError as exc:
        report["errors"] = 1
        report["items"].append({"index": 0, "errors": [str(exc)], "warnings": []})
        return report

    report["total"] = len(raw_items)
    seen: dict[str, int] = {}
    for index, raw in enumerate(raw_items, start=1):
        errors: list[str] = []
        warnings: list[str] = []
        item: QuestionImportItem | None = None
        try:
            item = QuestionImportItem.model_validate(raw)
        except ValidationError as exc:
            errors.extend(_validation_messages(exc))

        fingerprint = None
        if item:
            fingerprint = question_fingerprint(item)
            if fingerprint in seen:
                errors.append(f"与当前文件第 {seen[fingerprint]} 题重复")
            else:
                seen[fingerprint] = index
            if not item.source:
                warnings.append("source 为空")
            if len(item.solution.strip()) < 8:
                warnings.append("solution 过短，需人工确认解析质量")
            if not any(tag.startswith("kp:") for tag in item.tags):
                warnings.append("未提供显式 kp:<code>，verify 将通过名称或别名解析")

        report["items"].append(
            {
                "index": index,
                "question": str(raw.get("question", ""))[:100],
                "content_hash": fingerprint,
                "errors": errors,
                "warnings": warnings,
            }
        )
        report["errors"] += len(errors)
        report["warnings"] += len(warnings)
        if not errors:
            report["passed"] += 1
    return report


def lint_file(path: Path) -> dict[str, Any]:
    try:
        content = path.read_bytes()
    except OSError as exc:
        return {
            "command": "lint",
            "schema_version": "question-bank-report-v1",
            "filename": str(path),
            "total": 0,
            "passed": 0,
            "errors": 1,
            "warnings": 0,
            "items": [{"index": 0, "errors": [str(exc)], "warnings": []}],
        }
    return lint_content(content, filename=path.name)


async def _catalog(db: AsyncSession) -> dict[str, Any]:
    points = (
        await db.execute(
            select(
                KnowledgePoint.id,
                KnowledgePoint.code,
                KnowledgePoint.name,
                KnowledgePoint.subject,
                KnowledgePoint.level,
                KnowledgePoint.is_active,
            )
        )
    ).all()
    aliases = (
        await db.execute(
            select(
                KnowledgePointAlias.subject,
                KnowledgePointAlias.normalized_alias,
                KnowledgePoint.code,
            )
            .join(KnowledgePoint, KnowledgePoint.id == KnowledgePointAlias.knowledge_point_id)
            .where(KnowledgePointAlias.is_active.is_(True))
        )
    ).all()
    by_code = {row.code: row for row in points}
    by_name: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in points:
        if row.level == 3 and row.is_active:
            by_name[(row.subject, _normalize(row.name))].add(row.code)
    for row in aliases:
        by_name[(row.subject, row.normalized_alias)].add(row.code)
    return {"by_code": by_code, "by_name": by_name}


def _normalize(value: str) -> str:
    return "".join(value.split()).casefold()


def _resolve_code(
    item: QuestionImportItem,
    catalog: dict[str, Any],
) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    explicit = list(
        dict.fromkeys(tag[3:].strip() for tag in item.tags if tag.startswith("kp:"))
    )
    candidates: set[str] = set()
    if explicit:
        if len(explicit) != 1:
            return None, ["每题必须恰好提供一个 primary kp:<code>"]
        candidates.add(explicit[0])
    else:
        for name in item.knowledge_points:
            candidates.update(catalog["by_name"].get((item.subject, _normalize(name)), set()))

    resolved = {REDIRECTS.get(code, code) for code in candidates}
    if not resolved:
        return None, ["知识点无法解析到标准 code"]
    if len(resolved) != 1:
        return None, [f"知识点解析不唯一：{sorted(resolved)}"]
    code = next(iter(resolved))
    row = catalog["by_code"].get(code)
    if row is None:
        errors.append(f"知识点 code 不存在：{code}")
    elif code in FORBIDDEN_CODES:
        errors.append(f"知识点 code 不能作为 primary：{code}")
    elif row.level != 3 or not row.is_active:
        errors.append(f"知识点 code 不是启用的三级节点：{code}")
    elif row.subject != item.subject:
        errors.append(f"知识点 code 与题目学科不一致：{code}")

    if explicit and not errors:
        names_resolved: set[str] = set()
        for name in item.knowledge_points:
            names_resolved.update(
                REDIRECTS.get(value, value)
                for value in catalog["by_name"].get(
                    (item.subject, _normalize(name)),
                    set(),
                )
            )
        if names_resolved and names_resolved != {code}:
            errors.append(
                f"kp:<code> 与 knowledge_points 不一致：{sorted(names_resolved)}"
            )
    return (code if not errors else None), errors


async def verify_files(db: AsyncSession, paths: list[Path]) -> dict[str, Any]:
    catalog = await _catalog(db)
    file_reports = []
    all_hashes: set[str] = set()
    total = passed = error_count = warning_count = 0

    for path in paths:
        report = lint_file(path)
        try:
            raw_items = parse_question_json(path.read_bytes())
        except (OSError, QuestionFileError):
            raw_items = []
        for output, raw in zip(report["items"], raw_items, strict=False):
            if output["errors"]:
                continue
            item = QuestionImportItem.model_validate(raw)
            code, errors = _resolve_code(item, catalog)
            output["primary_code"] = code
            output["errors"].extend(errors)
            report["errors"] += len(errors)
            if errors:
                report["passed"] -= 1
            if output["content_hash"]:
                all_hashes.add(output["content_hash"])

        total += report["total"]
        passed += report["passed"]
        error_count += report["errors"]
        warning_count += report["warnings"]
        file_reports.append(report)

    database_hashes: set[str] = set()
    if all_hashes:
        database_hashes = set(
            (
                await db.execute(
                    select(Question.content_hash).where(Question.content_hash.in_(all_hashes))
                )
            ).scalars()
        )
    for report in file_reports:
        for item in report["items"]:
            if item.get("content_hash") in database_hashes:
                was_passing = not item["errors"]
                item["errors"].append("数据库中已存在相同题目")
                report["errors"] += 1
                error_count += 1
                if was_passing:
                    report["passed"] -= 1
                    passed -= 1

    return {
        "command": "verify",
        "schema_version": "question-bank-report-v1",
        "mapping_version": MAPPING_VERSION,
        "total": total,
        "passed": passed,
        "errors": error_count,
        "warnings": warning_count,
        "database_duplicates": len(database_hashes),
        "files": file_reports,
    }


async def coverage_report(db: AsyncSession, *, subject: str | None = None) -> dict[str, Any]:
    statement = (
        select(
            KnowledgePoint.code,
            KnowledgePoint.name,
            KnowledgePoint.subject,
            Question.id,
            Question.difficulty,
            Question.question_type,
        )
        .outerjoin(
            QuestionKnowledgePoint,
            (QuestionKnowledgePoint.knowledge_point_id == KnowledgePoint.id)
            & (QuestionKnowledgePoint.role == "primary"),
        )
        .outerjoin(
            Question,
            (Question.id == QuestionKnowledgePoint.question_id) & Question.is_active.is_(True),
        )
        .where(
            KnowledgePoint.level == 3,
            KnowledgePoint.is_active.is_(True),
            KnowledgePoint.code.not_in(set(REDIRECTS) | FORBIDDEN_CODES),
        )
    )
    if subject:
        statement = statement.where(KnowledgePoint.subject == subject)
    rows = (await db.execute(statement.order_by(KnowledgePoint.subject, KnowledgePoint.code))).all()
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        entry = grouped.setdefault(
            row.code,
            {
                "code": row.code,
                "name": row.name,
                "subject": row.subject,
                "question_count": 0,
                "difficulty_counts": {str(level): 0 for level in range(1, 6)},
                "type_counts": {},
            },
        )
        if row.id is not None:
            entry["question_count"] += 1
            entry["difficulty_counts"][str(row.difficulty)] += 1
            question_type = row.question_type.value
            entry["type_counts"][question_type] = (
                entry["type_counts"].get(question_type, 0) + 1
            )
    items = list(grouped.values())
    return {
        "command": "coverage",
        "mapping_version": MAPPING_VERSION,
        "subject": subject,
        "knowledge_point_count": len(items),
        "covered_count": sum(item["question_count"] > 0 for item in items),
        "question_count": sum(item["question_count"] for item in items),
        "items": items,
    }


async def difficulty_report(
    db: AsyncSession,
    *,
    subject: str | None = None,
) -> dict[str, Any]:
    coverage = await coverage_report(db, subject=subject)
    totals = Counter()
    for item in coverage["items"]:
        totals.update({int(level): count for level, count in item["difficulty_counts"].items()})
    count = sum(totals.values())
    weighted = sum(level * value for level, value in totals.items())
    return {
        "command": "difficulty",
        "subject": subject,
        "question_count": count,
        "average_difficulty": round(weighted / count, 2) if count else None,
        "difficulty_counts": {str(level): totals[level] for level in range(1, 6)},
        "items": coverage["items"],
    }


async def missing_report(
    db: AsyncSession,
    *,
    subject: str | None = None,
    minimum: int = 5,
) -> dict[str, Any]:
    coverage = await coverage_report(db, subject=subject)
    items = []
    for item in coverage["items"]:
        count = item["question_count"]
        if count >= minimum:
            continue
        items.append(
            {
                "code": item["code"],
                "name": item["name"],
                "subject": item["subject"],
                "question_count": count,
                "status": "empty" if count == 0 else "insufficient",
                "gap_to_minimum": minimum - count,
                "gap_to_10": max(0, 10 - count),
            }
        )
    return {
        "command": "missing",
        "mapping_version": MAPPING_VERSION,
        "subject": subject,
        "minimum": minimum,
        "missing_count": len(items),
        "empty_count": sum(item["status"] == "empty" for item in items),
        "insufficient_count": sum(item["status"] == "insufficient" for item in items),
        "items": items,
    }


async def verify_database(db: AsyncSession) -> dict[str, Any]:
    rows = (
        await db.execute(
            select(
                Question.id,
                Question.subject,
                QuestionKnowledgePoint.id.label("link_id"),
                KnowledgePoint.code,
                KnowledgePoint.subject.label("kp_subject"),
                KnowledgePoint.level,
                KnowledgePoint.is_active,
            )
            .outerjoin(
                QuestionKnowledgePoint,
                (QuestionKnowledgePoint.question_id == Question.id)
                & (QuestionKnowledgePoint.role == "primary"),
            )
            .outerjoin(
                KnowledgePoint,
                KnowledgePoint.id == QuestionKnowledgePoint.knowledge_point_id,
            )
            .where(Question.is_active.is_(True))
        )
    ).all()
    by_question: dict[int, list[Any]] = defaultdict(list)
    for row in rows:
        by_question[row.id].append(row)
    issues = []
    for question_id, question_rows in by_question.items():
        links = [row for row in question_rows if row.link_id is not None]
        if len(links) != 1:
            issues.append(
                {
                    "question_id": question_id,
                    "error": f"primary 数量为 {len(links)}，期望为 1",
                }
            )
            continue
        row = links[0]
        if row.level != 3 or not row.is_active or row.subject != row.kp_subject:
            issues.append(
                {
                    "question_id": question_id,
                    "error": f"primary 目标无效或跨学科：{row.code}",
                }
            )
    return {
        "command": "verify",
        "scope": "database",
        "active_question_count": len(by_question),
        "valid_question_count": len(by_question) - len(issues),
        "errors": len(issues),
        "issues": issues,
    }


def render_markdown(report: dict[str, Any]) -> str:
    command = report.get("command", "report")
    lines = [f"# Question Bank {command.title()} Report", ""]
    for key in (
        "filename",
        "mapping_version",
        "subject",
        "total",
        "passed",
        "errors",
        "warnings",
        "question_count",
        "knowledge_point_count",
        "covered_count",
        "missing_count",
        "empty_count",
        "insufficient_count",
        "average_difficulty",
    ):
        if key in report and report[key] is not None:
            lines.append(f"- {key}: {report[key]}")
    items = report.get("items", [])
    if items:
        lines.extend(
            [
                "",
                "## Items",
                "",
                "```json",
                json.dumps(items, ensure_ascii=False, indent=2),
                "```",
            ]
        )
    issues = report.get("issues", [])
    if issues:
        lines.extend(
            [
                "",
                "## Issues",
                "",
                "```json",
                json.dumps(issues, ensure_ascii=False, indent=2),
                "```",
            ]
        )
    return "\n".join(lines) + "\n"
