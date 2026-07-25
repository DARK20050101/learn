import pytest
from pydantic import ValidationError

from app.models.question import Question, QuestionType
from app.schemas.training_session import SubjectTrainingCreate
from app.services.subject_training import _matches, _target_difficulty


def make_question(
    *,
    subject: str = "数学",
    chapter: str = "函数",
    points: list[str] | None = None,
) -> Question:
    return Question(
        title="函数单调性",
        content="测试题",
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.single_choice,
        options=["A", "B"],
        correct_answer="A",
        difficulty=3,
        knowledge_points=points or ["函数单调性"],
    )


def test_subject_training_request_limits_question_count() -> None:
    with pytest.raises(ValidationError):
        SubjectTrainingCreate(subject="数学", question_count=21)
    with pytest.raises(ValidationError):
        SubjectTrainingCreate(subject="数学", difficulty=6)


def test_subject_training_accepts_standard_code_and_difficulty() -> None:
    data = SubjectTrainingCreate(
        subject="数学",
        chapter="函数",
        knowledge_point_code="MATH-FUNCTION-DOMAIN",
        difficulty=2,
        question_count=5,
    )
    assert data.knowledge_point_code == "MATH-FUNCTION-DOMAIN"
    assert data.difficulty == 2


def test_subject_training_filter_matches_selected_scope() -> None:
    question = make_question()
    assert _matches(
        question,
        SubjectTrainingCreate(
            subject="数学",
            chapter="函数",
            knowledge_point="函数单调性",
            question_count=5,
        ),
    )
    assert not _matches(
        question,
        SubjectTrainingCreate(subject="物理", question_count=5),
    )
    assert not _matches(
        question,
        SubjectTrainingCreate(subject="数学", chapter="数列", question_count=5),
    )


def test_subject_training_difficulty_follows_mastery_and_recent_errors() -> None:
    assert _target_difficulty(20, False) == 2
    assert _target_difficulty(90, False) == 4
    assert _target_difficulty(90, True) == 2
    assert _target_difficulty(60, False) == 3
