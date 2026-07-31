from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.knowledge_status import KnowledgeStatus
from app.models.student_answer import AnalysisStatus, StudentAnswer
from app.schemas.ai_analysis import (
    AIAnalysisInput,
    AIAnalysisResponse,
    AIAnalysisResult,
    AnalysisResponseStatus,
)
from app.services.llm import LLMService, llm_service
from app.services.student_answers import recalculate_mastery


async def _load_answer(
    db: AsyncSession, answer_id: int, user_id: int | None = None
) -> StudentAnswer | None:
    query = (
        select(StudentAnswer)
        .where(StudentAnswer.id == answer_id)
        .options(selectinload(StudentAnswer.question))
    )
    if user_id is not None:
        query = query.where(StudentAnswer.user_id == user_id)
    return await db.scalar(query)


def analysis_response(answer: StudentAnswer) -> AIAnalysisResponse:
    if answer.is_correct:
        return AIAnalysisResponse(
            answer_id=answer.id,
            status=AnalysisResponseStatus.not_required,
        )
    analysis = (
        AIAnalysisResult.model_validate(answer.ai_analysis)
        if answer.analysis_status == AnalysisStatus.completed and answer.ai_analysis
        else None
    )
    return AIAnalysisResponse(
        answer_id=answer.id,
        status=AnalysisResponseStatus(answer.analysis_status.value),
        analysis=analysis,
    )


async def get_answer_analysis(
    db: AsyncSession, answer_id: int, user_id: int
) -> AIAnalysisResponse | None:
    answer = await _load_answer(db, answer_id, user_id)
    return analysis_response(answer) if answer else None


async def retry_answer_analysis(
    db: AsyncSession,
    answer_id: int,
    user_id: int,
) -> tuple[AIAnalysisResponse | None, bool]:
    answer = await db.scalar(
        select(StudentAnswer)
        .where(
            StudentAnswer.id == answer_id,
            StudentAnswer.user_id == user_id,
        )
        .with_for_update()
    )
    if not answer:
        return None, False
    if answer.is_correct or answer.analysis_status in {
        AnalysisStatus.pending,
        AnalysisStatus.completed,
    }:
        return analysis_response(answer), False
    answer.analysis_status = AnalysisStatus.pending
    answer.ai_analysis = None
    await db.commit()
    return analysis_response(answer), True


def _canonical_gap(result: AIAnalysisResult, knowledge_points: list[str]) -> AIAnalysisResult:
    if result.knowledge_gap in knowledge_points:
        return result
    return result.model_copy(update={"knowledge_gap": knowledge_points[0]})


async def _apply_ai_gap(db: AsyncSession, answer: StudentAnswer, knowledge_gap: str) -> None:
    status = await db.scalar(
        select(KnowledgeStatus)
        .where(
            KnowledgeStatus.user_id == answer.user_id,
            KnowledgeStatus.subject == answer.question.subject,
            KnowledgeStatus.knowledge_point == knowledge_gap,
        )
        .with_for_update()
    )
    if not status:
        status = KnowledgeStatus(
            user_id=answer.user_id,
            subject=answer.question.subject,
            knowledge_point=knowledge_gap,
            attempt_count=0,
            correct_count=0,
            ai_gap_count=0,
            mastery_score=0,
        )
        db.add(status)
    status.ai_gap_count += 1
    recalculate_mastery(status)


async def analyze_answer(
    db: AsyncSession,
    answer_id: int,
    provider: LLMService = llm_service,
) -> AIAnalysisResponse | None:
    answer = await _load_answer(db, answer_id)
    if not answer:
        return None
    if answer.is_correct:
        if answer.analysis_status != AnalysisStatus.not_requested:
            answer.analysis_status = AnalysisStatus.not_requested
            answer.ai_analysis = None
            await db.commit()
        return analysis_response(answer)
    if answer.analysis_status == AnalysisStatus.completed:
        return analysis_response(answer)

    knowledge_points = answer.question.knowledge_points or [answer.question.title]
    data = AIAnalysisInput(
        question=answer.question.content,
        student_answer=answer.submitted_answer,
        correct_answer=answer.question.correct_answer,
        knowledge_points=knowledge_points,
        standard_solution=answer.question.explanation,
    )
    try:
        raw_result = await provider.analyze_mistake(data)
        result = AIAnalysisResult.model_validate(raw_result)
        result = _canonical_gap(result, knowledge_points)
        answer.ai_analysis = result.model_dump(mode="json")
        answer.analysis_status = AnalysisStatus.completed
        await _apply_ai_gap(db, answer, result.knowledge_gap)
        await db.commit()
    except Exception:
        await db.rollback()
        answer = await _load_answer(db, answer_id)
        if answer:
            answer.analysis_status = AnalysisStatus.failed
            answer.ai_analysis = None
            await db.commit()
    return analysis_response(answer) if answer else None


async def analyze_answer_background(answer_id: int) -> None:
    async with AsyncSessionLocal() as db:
        await analyze_answer(db, answer_id)
