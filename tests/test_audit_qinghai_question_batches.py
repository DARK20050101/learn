from pathlib import Path
from runpy import run_path

audit_question = run_path(
    str(Path(__file__).parents[1] / "scripts" / "audit_qinghai_question_batches.py")
)["audit_question"]


def question(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "question": "测试题",
        "options": ["甲", "乙", "丙", "丁"],
        "answer": "B",
        "solution": "逐项分析后，故选：B。",
    }
    payload.update(overrides)
    return payload


def test_clean_question_is_auto_passed() -> None:
    status, blockers, reasons = audit_question(question())
    assert status == "AUTO_PASS"
    assert blockers == []
    assert reasons == []


def test_answer_conflict_is_blocked() -> None:
    status, blockers, _ = audit_question(question(solution="故选：C。"))
    assert status == "BLOCK"
    assert blockers


def test_ocr_and_table_risks_require_review() -> None:
    status, _, reasons = audit_question(
        question(question=r"$\oint_U A$，见\begin{tabular}表格")
    )
    assert status == "REVIEW"
    assert len(reasons) == 2
