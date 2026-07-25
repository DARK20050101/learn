import importlib.util
import re
from pathlib import Path
from types import ModuleType


def load_revision() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260723_0009_link_questions_kp_v11.py"
    )
    spec = importlib.util.spec_from_file_location("revision_c_mapping", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


revision = load_revision()


def test_revision_c_contains_exactly_one_mapping_for_each_question() -> None:
    question_ids = [row[0] for row in revision.PRIMARY_MAPPINGS]
    assert revision.MAPPING_VERSION == "kp-mapping-v1.1"
    assert revision.SOURCE == "revision_c"
    assert len(question_ids) == 60
    assert set(question_ids) == set(range(1, 61))


def test_revision_c_mapping_matches_approved_dry_run_v2() -> None:
    report = (
        Path(__file__).parents[1] / "revision_c_dry_run_report_v2.md"
    ).read_text(encoding="utf-8")
    preview = [
        (int(question_id), code)
        for question_id, code in re.findall(
            r"^\|\s*(\d+)\s*\|[^|]*\|\s*`([^`]+)`\s*\|[^|]*\|\s*primary\s*\|",
            report,
            flags=re.MULTILINE,
        )
    ]
    assert preview == revision.PRIMARY_MAPPINGS


def test_revision_c_mapping_uses_subject_prefixes() -> None:
    for question_id, code in revision.PRIMARY_MAPPINGS:
        if question_id <= 20:
            assert code.startswith("MATH-")
        elif question_id <= 40:
            assert code.startswith("PHY-")
        else:
            assert code.startswith("ENG-")


def test_revision_c_does_not_target_redirected_or_ability_only_codes() -> None:
    forbidden = {
        "MATH-SET-INTERSECTION",
        "PHY-KINEMATICS-VELOCITY-EQUATION",
        "PHY-OPTICS-REFRACTION-PHENOMENON",
        "ENG-CLAUSE-RELATIVE-THAT",
        "ENG-CLAUSE-RELATIVE-WHERE",
        "ENG-GRAMMAR-MODAL-MUST",
        "ENG-WRITING-SENTENCE-EXPRESSION",
    }
    codes = {row[1] for row in revision.PRIMARY_MAPPINGS}
    assert codes.isdisjoint(forbidden)
