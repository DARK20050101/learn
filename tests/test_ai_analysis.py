from typing import Any

from app.models.knowledge_status import KnowledgeStatus
from app.models.question import Question, QuestionType
from app.models.student_answer import AnalysisStatus, StudentAnswer
from app.schemas.ai_analysis import AIAnalysisInput, AIAnalysisResult, MistakeType
from app.services.ai_analysis import analyze_answer, retry_answer_analysis


def make_answer(*, correct: bool = False) -> StudentAnswer:
    question = Question(
        id=10,
        title="函数单调性",
        content="函数 f(x)=2x+1 的单调性是什么？",
        subject="数学",
        question_type=QuestionType.single_choice,
        options=["递增", "递减"],
        correct_answer="递增",
        explanation="斜率大于零，所以函数递增。",
        difficulty=2,
        knowledge_points=["函数单调性"],
        tags=[],
        is_active=True,
    )
    return StudentAnswer(
        id=20,
        user_id=1,
        question_id=question.id,
        question=question,
        submitted_answer="递增" if correct else "递减",
        is_correct=correct,
        analysis_status=(AnalysisStatus.not_requested if correct else AnalysisStatus.pending),
    )


class FakeSession:
    def __init__(
        self,
        answer: StudentAnswer,
        knowledge: KnowledgeStatus | None = None,
    ) -> None:
        self.answer = answer
        self.knowledge = knowledge
        self.commits = 0
        self.rollbacks = 0
        self.added: list[object] = []

    async def scalar(self, query: object) -> Any:
        if "knowledge_status" in str(query):
            return self.knowledge
        return self.answer

    def add(self, value: object) -> None:
        self.added.append(value)
        if isinstance(value, KnowledgeStatus):
            self.knowledge = value

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class FakeLLM:
    def __init__(self, result: object | None = None, error: Exception | None = None) -> None:
        self.calls = 0
        self.input: AIAnalysisInput | None = None
        self.result = result or AIAnalysisResult(
            mistake_type=MistakeType.concept,
            reason="把斜率为正误认为函数递减。",
            knowledge_gap="函数单调性",
            suggestion="复习一次函数斜率与单调性的关系。",
            next_training="完成两道函数单调性基础题。",
        )
        self.error = error

    async def analyze_mistake(self, data: AIAnalysisInput) -> Any:
        self.calls += 1
        self.input = data
        if self.error:
            raise self.error
        return self.result


async def test_correct_answer_never_calls_llm() -> None:
    answer = make_answer(correct=True)
    db = FakeSession(answer)
    llm = FakeLLM()

    response = await analyze_answer(db, answer.id, llm)  # type: ignore[arg-type]

    assert response is not None
    assert response.status == "not_required"
    assert llm.calls == 0


async def test_wrong_answer_calls_once_and_saves_result() -> None:
    answer = make_answer()
    knowledge = KnowledgeStatus(
        user_id=1,
        subject="数学",
        knowledge_point="函数单调性",
        attempt_count=1,
        correct_count=0,
        ai_gap_count=0,
        mastery_score=0,
    )
    db = FakeSession(answer, knowledge)
    llm = FakeLLM()

    response = await analyze_answer(db, answer.id, llm)  # type: ignore[arg-type]
    repeated = await analyze_answer(db, answer.id, llm)  # type: ignore[arg-type]

    assert response is not None and response.analysis is not None
    assert repeated is not None
    assert llm.calls == 1
    assert answer.analysis_status == AnalysisStatus.completed
    assert answer.ai_analysis is not None
    assert answer.ai_analysis["mistake_type"] == "概念理解错误"
    assert knowledge.ai_gap_count == 1
    assert db.commits == 1


async def test_llm_input_is_built_from_database_entities() -> None:
    answer = make_answer()
    db = FakeSession(answer)
    llm = FakeLLM()

    await analyze_answer(db, answer.id, llm)  # type: ignore[arg-type]

    assert llm.input is not None
    assert llm.input.question == answer.question.content
    assert llm.input.student_answer == answer.submitted_answer
    assert llm.input.correct_answer == answer.question.correct_answer
    assert llm.input.knowledge_points == answer.question.knowledge_points


async def test_invalid_ai_structure_degrades_to_failed() -> None:
    answer = make_answer()
    db = FakeSession(answer)
    llm = FakeLLM(result={"reason": "缺少其他字段"})

    response = await analyze_answer(db, answer.id, llm)  # type: ignore[arg-type]

    assert response is not None
    assert response.status == "failed"
    assert answer.analysis_status == AnalysisStatus.failed
    assert answer.ai_analysis is None
    assert db.rollbacks == 1


async def test_llm_failure_does_not_remove_answer() -> None:
    answer = make_answer()
    db = FakeSession(answer)
    llm = FakeLLM(error=RuntimeError("provider unavailable"))

    response = await analyze_answer(db, answer.id, llm)  # type: ignore[arg-type]

    assert response is not None
    assert response.status == "failed"
    assert db.answer is answer
    assert answer.submitted_answer == "递减"
    assert answer.analysis_status == AnalysisStatus.failed


async def test_unknown_gap_is_normalized_to_question_knowledge_point() -> None:
    answer = make_answer()
    db = FakeSession(answer)
    llm = FakeLLM(
        result=AIAnalysisResult(
            mistake_type=MistakeType.other,
            reason="知识点判断不准确。",
            knowledge_gap="模型生成的未知知识点",
            suggestion="复习基础概念。",
            next_training="完成基础题。",
        )
    )

    response = await analyze_answer(db, answer.id, llm)  # type: ignore[arg-type]

    assert response is not None and response.analysis is not None
    assert response.analysis.knowledge_gap == "函数单调性"
    assert db.knowledge is not None
    assert db.knowledge.knowledge_point == "函数单调性"


async def test_failed_analysis_can_be_marked_pending_for_one_retry() -> None:
    answer = make_answer()
    answer.analysis_status = AnalysisStatus.failed
    db = FakeSession(answer)

    response, scheduled = await retry_answer_analysis(db, answer.id, answer.user_id)  # type: ignore[arg-type]

    assert response is not None
    assert response.status == "pending"
    assert scheduled is True
    assert answer.analysis_status == AnalysisStatus.pending
    assert db.commits == 1


async def test_pending_analysis_is_not_scheduled_twice() -> None:
    answer = make_answer()
    db = FakeSession(answer)

    response, scheduled = await retry_answer_analysis(db, answer.id, answer.user_id)  # type: ignore[arg-type]

    assert response is not None
    assert response.status == "pending"
    assert scheduled is False
    assert db.commits == 0
