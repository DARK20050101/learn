import importlib.util
from collections import Counter
from pathlib import Path

PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20260730_0013_add_three_subject_knowledge_catalog.py"
)
SPEC = importlib.util.spec_from_file_location("three_subject_catalog_revision", PATH)
assert SPEC and SPEC.loader
REVISION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVISION)


def test_catalog_has_expected_three_level_shape() -> None:
    assert len(REVISION.ROOTS) == 3
    assert len(REVISION.MODULES) == 18
    assert len(REVISION.POINTS) == 54
    assert Counter(row[2] for row in REVISION.POINTS) == {
        "语文": 18,
        "化学": 18,
        "生物": 18,
    }


def test_catalog_codes_are_unique_and_parents_exist() -> None:
    all_rows = [*REVISION.ROOTS, *REVISION.MODULES, *REVISION.POINTS]
    codes = [row[0] for row in all_rows]
    assert len(codes) == len(set(codes)) == 75

    root_codes = {row[0] for row in REVISION.ROOTS}
    module_codes = {row[0] for row in REVISION.MODULES}
    assert {row[3] for row in REVISION.MODULES} <= root_codes
    assert {row[3] for row in REVISION.POINTS} <= module_codes


def test_catalog_code_prefix_matches_subject() -> None:
    prefixes = {"语文": "CHN-", "化学": "CHEM-", "生物": "BIO-"}
    for code, _name, subject, *_rest in REVISION.POINTS:
        assert code.startswith(prefixes[subject])
