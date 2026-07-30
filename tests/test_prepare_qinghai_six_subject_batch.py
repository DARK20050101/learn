from pathlib import Path
from runpy import run_path

SELECTIONS = run_path(
    str(Path(__file__).parents[1] / "scripts" / "prepare_qinghai_six_subject_batch.py")
)["SELECTIONS"]


def test_selection_contains_ten_unique_questions_per_subject() -> None:
    assert len(SELECTIONS) == 6
    assert all(len(spec["items"]) == 10 for spec in SELECTIONS.values())
    assert sum(len(spec["items"]) for spec in SELECTIONS.values()) == 60

    source_keys = {
        (spec["file"], source_index)
        for spec in SELECTIONS.values()
        for source_index in spec["items"]
    }
    assert len(source_keys) == 60


def test_selection_uses_standard_knowledge_point_codes() -> None:
    for spec in SELECTIONS.values():
        for _, code, standard_name, difficulty in spec["items"].values():
            assert code.startswith(
                ("CHN-", "MATH-", "ENG-", "PHY-", "CHEM-", "BIO-")
            )
            assert standard_name
            assert difficulty in {2, 3}
