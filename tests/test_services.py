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


def test_evaluate_fill_blank_accepts_synonym_list() -> None:
    q = question(QuestionType.fill_blank, ["单调递增", "单调上升"])
    assert evaluate_answer(q, "单调递增")
    assert evaluate_answer(q, "单调上升")


def test_evaluate_fill_blank_is_lenient() -> None:
    q = question(QuestionType.fill_blank, ["光合作用"])
    assert evaluate_answer(q, " 光 合 作 用 ")
    assert evaluate_answer(q, "光合作用。")
    assert evaluate_answer(q, "光合作用，")


def test_evaluate_fill_blank_normalizes_width_and_case() -> None:
    q = question(QuestionType.fill_blank, ["NaHCO3"])
    assert evaluate_answer(q, "ｎａＨＣＯ３")
    assert evaluate_answer(q, "nahco3")


def test_evaluate_fill_blank_rejects_wrong_or_empty() -> None:
    q = question(QuestionType.fill_blank, ["光合作用"])
    assert not evaluate_answer(q, "呼吸作用")
    assert not evaluate_answer(q, "   ")
