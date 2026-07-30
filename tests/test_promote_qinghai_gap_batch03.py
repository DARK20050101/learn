from pathlib import Path
from runpy import run_path

MODULE = run_path(
    str(Path(__file__).parents[1] / "scripts" / "promote_qinghai_gap_batch03.py")
)
REVIEW = MODULE["REVIEW"]
promote = MODULE["promote"]


def test_promote_is_fail_closed_and_applies_semantic_review() -> None:
    questions = [
        {
            "source": f"source-{index}",
            "chapter": "old",
            "knowledge_points": ["old"],
            "difficulty": 3,
            "tags": ["kp:old", "review:required", "keep"],
            "question": "question",
            "options": ["A", "B", "C", "D"],
            "solution": "solution",
        }
        for index in REVIEW
    ]

    candidate, report = promote({"questions": questions, "source_commit": "abc"})

    assert report["input_questions"] == 49
    assert report["release_questions"] == 44
    assert report["rejected"] == 5
    assert len(candidate["questions"]) == 44
    assert candidate["questions"][0]["knowledge_points"] == ["反应速率与化学平衡"]
    assert candidate["questions"][0]["difficulty"] == 3
    assert "kp:CHEM-REACTION-RATE-EQUILIBRIUM" in candidate["questions"][0]["tags"]
    assert "review:revise-semantic" in candidate["questions"][0]["tags"]
    assert "review:required" not in candidate["questions"][0]["tags"]


def test_promote_rejects_unexpected_input_size() -> None:
    try:
        promote({"questions": []})
    except ValueError as exc:
        assert "expected 49 questions" in str(exc)
    else:
        raise AssertionError("unexpected input size must fail")
