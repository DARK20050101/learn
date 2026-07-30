import sys
from pathlib import Path
from runpy import run_path

sys.path.insert(0, str(Path(__file__).parents[1]))

SELECTIONS = run_path(
    str(Path(__file__).parents[1] / "scripts" / "prepare_qinghai_six_subject_batch02.py")
)["SELECTIONS"]
FIRST_BATCH_SELECTIONS = run_path(
    str(Path(__file__).parents[1] / "scripts" / "prepare_qinghai_six_subject_batch.py")
)["SELECTIONS"]


def test_batch02_has_ten_unique_questions_per_subject() -> None:
    assert len(SELECTIONS) == 6
    assert all(len(spec["items"]) == 10 for spec in SELECTIONS.values())
    assert sum(len(spec["items"]) for spec in SELECTIONS.values()) == 60

    source_keys = {
        (spec["file"], source_index)
        for spec in SELECTIONS.values()
        for source_index in spec["items"]
    }
    assert len(source_keys) == 60


def test_batch02_uses_supported_difficulty_and_standard_codes() -> None:
    for spec in SELECTIONS.values():
        for _, code, standard_name, difficulty in spec["items"].values():
            assert code.startswith(
                ("CHN-", "MATH-", "ENG-", "PHY-", "CHEM-", "BIO-")
            )
            assert standard_name
            assert difficulty in {2, 3}


def test_batch02_does_not_reuse_batch01_source_questions() -> None:
    first_batch_keys = {
        (spec["file"], source_index)
        for spec in FIRST_BATCH_SELECTIONS.values()
        for source_index in spec["items"]
    }
    second_batch_keys = {
        (spec["file"], source_index)
        for spec in SELECTIONS.values()
        for source_index in spec["items"]
    }
    assert first_batch_keys.isdisjoint(second_batch_keys)
