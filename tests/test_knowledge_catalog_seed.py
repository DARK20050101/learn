import importlib.util
from pathlib import Path
from types import ModuleType


def load_revision() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260723_0007_seed_knowledge_catalog.py"
    )
    spec = importlib.util.spec_from_file_location("knowledge_catalog_revision", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


revision = load_revision()


def test_kp_mapping_v1_has_58_unique_level_three_codes() -> None:
    codes = [row[0] for row in revision.LEVEL_THREE]
    assert revision.MAPPING_VERSION == "kp-mapping-v1"
    assert len(codes) == 58
    assert len(set(codes)) == 58
    assert sum(code.startswith("MATH-") for code in codes) == 20
    assert sum(code.startswith("PHY-") for code in codes) == 20
    assert sum(code.startswith("ENG-") for code in codes) == 18


def test_every_seeded_node_has_a_valid_parent() -> None:
    level_one_codes = {row[0] for row in revision.LEVEL_ONE}
    level_two_codes = {row[0] for row in revision.LEVEL_TWO}
    assert all(row[3] in level_one_codes for row in revision.LEVEL_TWO)
    assert all(row[3] in level_two_codes for row in revision.LEVEL_THREE)


def test_all_knowledge_point_codes_are_globally_unique() -> None:
    rows = revision.LEVEL_ONE + revision.LEVEL_TWO + revision.LEVEL_THREE
    codes = [row[0] for row in rows]
    assert len(codes) == len(set(codes))


def test_aliases_are_unique_and_reference_seeded_codes() -> None:
    codes = {row[0] for row in revision.LEVEL_THREE}
    normalized_keys = {
        (subject, revision._normalize_alias(alias))
        for subject, alias, _ in revision.ALIASES
    }
    assert len(normalized_keys) == len(revision.ALIASES)
    assert all(code in codes for _, _, code in revision.ALIASES)


def test_known_incorrect_labels_are_not_global_aliases() -> None:
    aliases = {(subject, alias) for subject, alias, _ in revision.ALIASES}
    assert ("英语", "动词辨析") not in aliases
    assert ("英语", "形容词辨析") not in aliases
    assert ("英语", "动名词") not in aliases
    assert ("英语", "句子翻译") not in aliases
