import importlib.util
from pathlib import Path
from types import ModuleType


def load_revision() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260723_0008_add_kp_mapping_v11_points.py"
    )
    spec = importlib.util.spec_from_file_location("kp_mapping_v11_revision", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


revision = load_revision()


def test_v11_adds_exactly_six_unique_codes() -> None:
    codes = [row[0] for row in revision.V11_ADDITIONS]
    assert revision.MAPPING_VERSION == "kp-mapping-v1.1"
    assert len(codes) == 6
    assert len(set(codes)) == 6


def test_v11_additions_have_expected_subject_distribution() -> None:
    subjects = [row[2] for row in revision.V11_ADDITIONS]
    assert subjects.count("数学") == 1
    assert subjects.count("物理") == 2
    assert subjects.count("英语") == 3


def test_v11_additions_reference_expected_existing_parents() -> None:
    parents = {row[3] for row in revision.V11_ADDITIONS}
    assert parents == {
        "MATH-SET",
        "PHY-KINEMATICS",
        "PHY-OPTICS",
        "ENG-CLAUSE",
        "ENG-GRAMMAR",
        "ENG-NONFINITE",
    }
