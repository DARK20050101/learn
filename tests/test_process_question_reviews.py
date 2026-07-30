import json
from pathlib import Path
from runpy import run_path

MODULE = run_path(
    str(Path(__file__).parents[1] / "scripts" / "process_question_reviews.py")
)
process = MODULE["process"]
ReviewProcessingError = MODULE["ReviewProcessingError"]


def write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def question(source: str) -> dict[str, object]:
    return {
        "source": source,
        "title": source,
        "subject": "数学",
        "chapter": "集合",
        "knowledge_points": ["集合运算"],
        "question": "原题",
        "options": ["A", "B"],
        "answer": "A",
        "solution": "解析",
        "tags": ["review:required", "kp:MATH-SET"],
    }


def test_pass_is_copied_and_revise_is_patched(tmp_path: Path) -> None:
    queue = write(
        tmp_path / "queue.json",
        {"questions": [question("pass"), question("revise")]},
    )
    result = write(
        tmp_path / "result.json",
        {
            "reviews": [
                {"source": "pass", "decision": "PASS", "note": ""},
                {"source": "revise", "decision": "REVISE", "note": "显示错误"},
            ]
        },
    )
    revisions = write(
        tmp_path / "revisions.json",
        {
            "revisions": {
                "revise": {
                    "reason": "修复显示",
                    "updates": {"question": "修订题"},
                }
            }
        },
    )

    candidate, report = process(queue, result, revisions)

    assert [item["question"] for item in candidate["questions"]] == ["原题", "修订题"]
    assert candidate["questions"][0]["tags"][-1] == "review:passed"
    assert candidate["questions"][1]["tags"][-1] == "review:revised"
    assert report["release_questions"] == 2


def test_incomplete_review_fails_closed(tmp_path: Path) -> None:
    queue = write(tmp_path / "queue.json", {"questions": [question("pending")]})
    result = write(
        tmp_path / "result.json",
        {"reviews": [{"source": "pending", "decision": "", "note": ""}]},
    )
    revisions = write(tmp_path / "revisions.json", {"revisions": {}})

    try:
        process(queue, result, revisions)
    except ReviewProcessingError as error:
        assert "incomplete" in str(error)
    else:
        raise AssertionError("incomplete reviews must fail")
