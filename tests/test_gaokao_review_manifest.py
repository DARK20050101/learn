import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "apply_gaokao_review.py"
SPEC = importlib.util.spec_from_file_location("apply_gaokao_review", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

DIFFICULTIES = MODULE.DIFFICULTIES
REVISE_ITEMS = MODULE.REVISE_ITEMS
reviewed_tags = MODULE.reviewed_tags


def test_review_manifest_covers_exactly_fifty_questions() -> None:
    assert set(DIFFICULTIES) == set(range(1, 51))
    assert len(REVISE_ITEMS) == 13
    assert len(set(DIFFICULTIES) - REVISE_ITEMS) == 37
    assert set(DIFFICULTIES.values()) <= {1, 2, 3, 4, 5}


def test_reviewed_tags_replace_pending_review_state() -> None:
    assert reviewed_tags(
        ["kp:MATH-FUNCTION-PARITY", "review:required"],
        passed=True,
    ) == ["kp:MATH-FUNCTION-PARITY", "review:passed"]
    assert reviewed_tags(
        ["origin:external", "review:passed"],
        passed=False,
    ) == ["origin:external", "review:revise"]
