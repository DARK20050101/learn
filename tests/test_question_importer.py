import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.question_import import ImportStatus, QuestionImportBatch
from app.schemas.question_import import QuestionImportItem
from app.services.question_importer import (
    QuestionFileError,
    import_questions,
    parse_question_json,
    question_fingerprint,
)


def valid_question(**changes: object) -> dict:
    item = {
        "subject": "数学",
        "chapter": "函数",
        "knowledge_points": ["函数单调性"],
        "difficulty": 2,
        "type": "single_choice",
        "question": "函数 f(x)=2x+1 的单调性是？",
        "options": ["递增", "递减", "不确定"],
        "answer": "A",
        "solution": "斜率 2 大于 0，所以函数单调递增。",
        "source": "测试",
    }
    item.update(changes)
    return item


def test_single_choice_letter_is_normalized_to_option() -> None:
    item = QuestionImportItem.model_validate(valid_question())
    assert item.answer == "递增"


def test_choice_answer_must_exist_in_options() -> None:
    with pytest.raises(ValidationError, match="不在 options 中"):
        QuestionImportItem.model_validate(valid_question(answer="D"))


def test_question_fingerprint_normalizes_whitespace() -> None:
    first = QuestionImportItem.model_validate(valid_question())
    second = QuestionImportItem.model_validate(
        valid_question(question="  函数   f(x)=2x+1 的单调性是？  ")
    )
    assert question_fingerprint(first) == question_fingerprint(second)


def test_parse_supported_json_roots() -> None:
    item = valid_question()
    assert len(parse_question_json(json.dumps(item).encode())) == 1
    assert len(parse_question_json(json.dumps([item]).encode())) == 1
    assert len(parse_question_json(json.dumps({"questions": [item]}).encode())) == 1


def test_parse_rejects_empty_file() -> None:
    with pytest.raises(QuestionFileError, match="不能为空"):
        parse_question_json(b"[]")


class FakeResult:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class FakeSession:
    def __init__(self, rowcounts: list[int]) -> None:
        self.rowcounts = iter(rowcounts)
        self.batch: QuestionImportBatch | None = None
        self.committed = False

    def add(self, value: object) -> None:
        assert isinstance(value, QuestionImportBatch)
        self.batch = value

    async def flush(self) -> None:
        assert self.batch is not None
        self.batch.id = 42

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(next(self.rowcounts))

    async def commit(self) -> None:
        self.committed = True


async def test_import_reports_invalid_and_in_file_duplicate() -> None:
    first = valid_question()
    invalid = valid_question(question="", answer="D")
    content = json.dumps([first, first, invalid], ensure_ascii=False).encode()
    db = FakeSession([1])

    result = await import_questions(db, filename="questions.json", content=content)  # type: ignore[arg-type]

    assert result.status == ImportStatus.completed_with_errors
    assert result.total_count == 3
    assert result.imported_count == 1
    assert result.duplicate_count == 1
    assert result.failed_count == 1
    assert len(result.errors) == 2
    assert db.committed


async def test_import_reports_database_duplicate() -> None:
    db = FakeSession([0])
    content = json.dumps([valid_question()], ensure_ascii=False).encode()

    result = await import_questions(db, filename="questions.json", content=content)  # type: ignore[arg-type]

    assert result.imported_count == 0
    assert result.duplicate_count == 1
    assert result.failed_count == 0


async def test_malformed_file_is_written_to_batch_log() -> None:
    db = FakeSession([])

    with pytest.raises(QuestionFileError):
        await import_questions(db, filename="broken.json", content=b"not-json")  # type: ignore[arg-type]

    assert db.batch is not None
    assert db.batch.status == ImportStatus.failed
    assert db.batch.failed_count == 1
    assert db.batch.errors
    assert db.committed


def test_sample_banks_contain_twenty_valid_questions_each() -> None:
    root = Path(__file__).parents[1] / "data" / "questions"
    for filename in ("math.json", "physics.json", "english.json"):
        questions = parse_question_json((root / filename).read_bytes())
        assert len(questions) == 20
        assert all(QuestionImportItem.model_validate(question) for question in questions)
