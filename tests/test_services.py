from app.models.question import Question, QuestionType
from app.services.student_answers import evaluate_answer


def question(question_type: QuestionType, answer: object) -> Question:
    return Question(
        title="测试题",
        content="题干",
        subject="数学",
        question_type=question_type,
        correct_answer=answer,
        knowledge_points=["集合"],
    )


def test_evaluate_multiple_choice_ignores_order() -> None:
    assert evaluate_answer(question(QuestionType.multiple_choice, ["A", "C"]), ["c", "A"])


def test_evaluate_short_answer_normalizes_text() -> None:
    assert evaluate_answer(question(QuestionType.short_answer, "定义域"), "  定义域 ")
