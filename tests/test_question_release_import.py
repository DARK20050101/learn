import json

from app.cli.question_bank_release import build_parser
from app.schemas.question_import import QuestionImportItem
from app.services.question_importer import question_fingerprint
from app.services.question_release_import import (
    RELEASE_LOCK_KEY,
    QuestionReleaseImportError,
    _question_business_hash,
)


def test_release_cli_supports_dry_run_and_report_dir() -> None:
    args = build_parser().parse_args(
        [
            "batch.json",
            "--dry-run",
            "--report-dir",
            "reports",
            "--mapping-version",
            "kp-mapping-v1.1",
        ]
    )
    assert args.file.name == "batch.json"
    assert args.dry_run is True
    assert args.report_dir.name == "reports"
    assert args.mapping_version == "kp-mapping-v1.1"


def test_release_lock_key_is_stable() -> None:
    assert RELEASE_LOCK_KEY == "question-bank-release-import-v1"


def test_release_error_keeps_structured_details() -> None:
    errors = [{"index": 1, "errors": ["冲突"]}]
    exc = QuestionReleaseImportError(errors)
    assert exc.errors == errors


def test_fingerprint_is_stable_for_release_reruns() -> None:
    payload = {
        "subject": "数学",
        "chapter": "函数",
        "knowledge_points": ["函数单调性"],
        "difficulty": 2,
        "type": "single_choice",
        "question": "函数 f(x)=2x+1 的单调性是？",
        "options": ["递增", "递减"],
        "answer": "A",
        "solution": "斜率大于零，因此单调递增。",
        "source": "测试",
        "tags": ["kp:MATH-FUNCTION-MONOTONICITY"],
    }
    first = QuestionImportItem.model_validate(payload)
    second = QuestionImportItem.model_validate(json.loads(json.dumps(payload)))
    assert question_fingerprint(first) == question_fingerprint(second)


def test_empty_business_snapshot_hash_is_deterministic() -> None:
    assert _question_business_hash([]) == _question_business_hash([])
