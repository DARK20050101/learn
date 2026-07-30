import importlib.util
from pathlib import Path

PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260726_0012_add_review_knowledge_points.py"
)
SPEC = importlib.util.spec_from_file_location("review_kp_revision", PATH)
assert SPEC and SPEC.loader
REVISION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVISION)


def test_review_additions_are_three_unique_level_three_targets() -> None:
    codes = [row[0] for row in REVISION.REVIEW_ADDITIONS]
    assert codes == [
        "MATH-VECTOR-DOT-PRODUCT",
        "ENG-VOCAB-CONTEXT-ADVERB",
        "ENG-VOCAB-SITUATIONAL-COMMUNICATION",
    ]
    assert len(set(codes)) == 3


def test_review_additions_use_existing_subject_parents() -> None:
    assert {(row[2], row[3]) for row in REVISION.REVIEW_ADDITIONS} == {
        ("数学", "MATH-VECTOR"),
        ("英语", "ENG-VOCAB"),
    }
