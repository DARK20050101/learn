import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "data" / "question_bank" / "drafts" / "gaokao_bench_batch01_v1.json"
SCRIPT = ROOT / "scripts" / "prepare_gaokao_revision.py"
SPEC = importlib.util.spec_from_file_location("prepare_gaokao_revision", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
prepare = MODULE.prepare


def test_revision_preserves_answers_and_approves_all_questions() -> None:
    original = __import__("json").loads(SOURCE.read_text(encoding="utf-8"))
    revised = prepare(SOURCE)
    assert len(revised["questions"]) == 50
    assert [item["answer"] for item in revised["questions"]] == [
        item["answer"] for item in original["questions"]
    ]
    assert all("review:passed" in item["tags"] for item in revised["questions"])
    assert all("review:required" not in item["tags"] for item in revised["questions"])


def test_revision_uses_new_review_knowledge_points() -> None:
    revised = prepare(SOURCE)["questions"]
    assert "kp:MATH-VECTOR-DOT-PRODUCT" in revised[16]["tags"]
    assert "kp:ENG-VOCAB-SITUATIONAL-COMMUNICATION" in revised[42]["tags"]
    assert "kp:ENG-VOCAB-CONTEXT-ADVERB" in revised[46]["tags"]
