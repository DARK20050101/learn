import sys
from pathlib import Path
from runpy import run_path

sys.path.insert(0, str(Path(__file__).parents[1]))
MODULE = run_path(
    str(Path(__file__).parents[1] / "scripts" / "prepare_qinghai_english_gap_batch04.py")
)
SELECTIONS = MODULE["SELECTIONS"]


def test_selections_are_single_purpose_and_unique() -> None:
    assert len(SELECTIONS) == 12
    assert len(set(SELECTIONS)) == len(SELECTIONS)
    assert all(code.startswith("ENG-") for _, code, _, _ in SELECTIONS.values())
    assert all(difficulty in {2, 3} for *_, difficulty in SELECTIONS.values())
