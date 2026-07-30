from pathlib import Path
from runpy import run_path

MODULE = run_path(
    str(Path(__file__).parents[1] / "scripts" / "prepare_agieval_qinghai_2023_batch06.py")
)
EXPECTED_COMMIT = MODULE["EXPECTED_COMMIT"]
SELECTIONS = MODULE["SELECTIONS"]


def test_selection_manifest_is_small_unique_and_complete() -> None:
    assert len(SELECTIONS) == 11
    identities = {(item.dataset, item.row) for item in SELECTIONS}
    assert len(identities) == len(SELECTIONS)
    assert {item.subject for item in SELECTIONS} == {"物理", "化学", "生物"}
    assert all(item.code.startswith(("PHY-", "CHEM-", "BIO-")) for item in SELECTIONS)
    assert all(item.difficulty in {2, 3} for item in SELECTIONS)
    assert all(
        "正确答案为" in item.solution or "错误叙述为" in item.solution
        for item in SELECTIONS
    )


def test_source_commit_is_fully_pinned() -> None:
    assert len(EXPECTED_COMMIT) == 40
    assert all(character in "0123456789abcdef" for character in EXPECTED_COMMIT)
