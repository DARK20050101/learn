import importlib.util
import re
from pathlib import Path
from types import ModuleType


def load_revision() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260723_0010_backfill_knowledge_status_ids.py"
    )
    spec = importlib.util.spec_from_file_location("revision_d1_mapping", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


revision = load_revision()


def test_revision_d1_maps_exactly_the_18_approved_statuses() -> None:
    status_ids = [row[0] for row in revision.STATUS_MAPPINGS]
    assert revision.MAPPING_VERSION == "kp-mapping-v1.1"
    assert len(status_ids) == 18
    assert set(status_ids) == set(range(1, 19))


def test_revision_d1_mapping_matches_dry_run_report() -> None:
    report = (
        Path(__file__).parents[1] / "revision_d_dry_run_report.md"
    ).read_text(encoding="utf-8")
    preview = [
        (int(status_id), int(user_id), subject, legacy_name.strip(), code)
        for status_id, user_id, subject, legacy_name, code in re.findall(
            r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(数学|物理|英语)\s*\|"
            r"\s*([^|]+?)\s*\|(?:[^|]*\|){5}\s*`([^`]+)`\s*\|",
            report,
            flags=re.MULTILINE,
        )
    ]
    assert preview == revision.STATUS_MAPPINGS


def test_revision_d1_targets_twelve_standard_nodes() -> None:
    codes = {row[4] for row in revision.STATUS_MAPPINGS}
    assert len(codes) == 12


def test_revision_d1_only_declares_backfill_columns() -> None:
    source = Path(revision.__file__).read_text(encoding="utf-8")
    assert ".values(" in source
    assert "knowledge_point_id=" in source
    assert "mapping_version=" in source
    assert "mapped_at=" in source
    assert "attempt_count=" not in source
    assert "correct_count=" not in source
    assert "ai_gap_count=" not in source
    assert "mastery_score=" not in source
