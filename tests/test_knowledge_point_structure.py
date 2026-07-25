from app.database import Base
from app.models.knowledge_point import (
    KnowledgePoint,
    KnowledgePointAlias,
    KnowledgeStatusMigrationBackup,
    QuestionKnowledgePoint,
)
from app.models.knowledge_status import KnowledgeStatus


def test_revision_a_tables_are_registered() -> None:
    expected = {
        "knowledge_points",
        "knowledge_point_aliases",
        "question_knowledge_points",
        "knowledge_status_migration_backups",
    }
    assert expected.issubset(Base.metadata.tables)


def test_knowledge_status_expansion_is_nullable() -> None:
    assert KnowledgeStatus.__table__.c.knowledge_point_id.nullable
    assert KnowledgeStatus.__table__.c.mapping_version.nullable
    assert KnowledgeStatus.__table__.c.mapped_at.nullable


def test_knowledge_point_code_and_alias_are_unique() -> None:
    knowledge_constraints = {
        constraint.name for constraint in KnowledgePoint.__table__.constraints
    }
    alias_constraints = {
        constraint.name for constraint in KnowledgePointAlias.__table__.constraints
    }
    assert "uq_knowledge_points_code" in knowledge_constraints
    assert "uq_knowledge_point_alias_subject_normalized" in alias_constraints


def test_question_knowledge_point_constraints_exist() -> None:
    constraints = {
        constraint.name for constraint in QuestionKnowledgePoint.__table__.constraints
    }
    indexes = {index.name for index in QuestionKnowledgePoint.__table__.indexes}
    assert "uq_question_knowledge_point" in constraints
    assert "ck_question_knowledge_point_role" in constraints
    assert "ck_question_knowledge_point_weight" in constraints
    assert "uq_question_primary_knowledge_point" in indexes


def test_migration_backup_has_idempotency_constraint() -> None:
    constraints = {
        constraint.name
        for constraint in KnowledgeStatusMigrationBackup.__table__.constraints
    }
    assert "uq_knowledge_status_backup_batch_original" in constraints
