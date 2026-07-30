from pathlib import Path
from runpy import run_path

MODULE = run_path(
    str(Path(__file__).parents[1] / "scripts" / "prepare_agieval_chemistry_2023_batch07.py")
)
SELECTIONS = MODULE["SELECTIONS"]
EXPECTED_COMMIT = MODULE["EXPECTED_COMMIT"]


def test_chemistry_selections_are_fixed_and_unique() -> None:
    assert len(SELECTIONS) == 12
    assert len({item.row for item in SELECTIONS}) == len(SELECTIONS)
    assert all(item.code.startswith("CHEM-") for item in SELECTIONS)
    assert all(item.difficulty in {2, 3} for item in SELECTIONS)
    assert all(len(item.solution) >= 45 for item in SELECTIONS)


def test_source_is_pinned_to_full_commit() -> None:
    assert len(EXPECTED_COMMIT) == 40
