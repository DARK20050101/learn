from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.ai_analysis import AIAnalysisResponse
from app.schemas.common import Page
from app.schemas.student_answer import (
    AnswerFeedbackRead,
    AnswerFeedbackUpdate,
    AnswerResult,
    AnswerStats,
    AnswerSubmit,
    StudentAnswerRead,
)
from app.services import ai_analysis, questions
from app.services import student_answers as service

router = APIRouter(prefix="/student-answers", tags=["答题记录"])


@router.post("", response_model=AnswerResult, status_code=status.HTTP_201_CREATED)
async def submit_answer(
    data: AnswerSubmit,
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> AnswerResult:
    question = await questions.get_question(db, data.question_id)
    answer, created = await service.create_answer(db, user.id, question, data)
    if created and not answer.is_correct:
        background_tasks.add_task(ai_analysis.analyze_answer_background, answer.id)
    return AnswerResult(
        **StudentAnswerRead.model_validate(answer).model_dump(),
        correct_answer=question.correct_answer,
        explanation=question.explanation,
    )


@router.get("", response_model=Page[StudentAnswerRead])
async def list_answers(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[StudentAnswerRead]:
    items, total = await service.list_answers(db, user.id, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/stats", response_model=AnswerStats)
async def stats(db: DbSession, user: CurrentUser) -> AnswerStats:
    return await service.get_stats(db, user.id)


@router.get("/{answer_id}/analysis", response_model=AIAnalysisResponse)
async def get_analysis(answer_id: int, db: DbSession, user: CurrentUser) -> AIAnalysisResponse:
    result = await ai_analysis.get_answer_analysis(db, answer_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="答题记录不存在")
    return result


@router.patch("/{answer_id}/feedback", response_model=AnswerFeedbackRead)
async def update_feedback(
    answer_id: int,
    data: AnswerFeedbackUpdate,
    db: DbSession,
    user: CurrentUser,
) -> AnswerFeedbackRead:
    answer = await service.update_feedback(db, answer_id, user.id, data.difficulty_feedback)
    if not answer:
        raise HTTPException(status_code=404, detail="答题记录不存在")
    return AnswerFeedbackRead(
        answer_id=answer.id,
        difficulty_feedback=answer.difficulty_feedback,
    )
