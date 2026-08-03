from fastapi import APIRouter, BackgroundTasks, Query, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import Page
from app.schemas.student_answer import AnswerResult, StudentAnswerRead
from app.schemas.training_session import (
    SubjectTrainingCatalog,
    SubjectTrainingCreate,
    TrainingAnswerSubmit,
    TrainingSessionItemRead,
    TrainingSessionRead,
    TrainingSessionSummary,
)
from app.services import ai_analysis, fill_blank_training, subject_training
from app.services import training_sessions as service

router = APIRouter(prefix="/training-sessions", tags=["通用训练"])
item_router = APIRouter(prefix="/training-session-items", tags=["通用训练"])


@router.get("/fill/catalog", response_model=SubjectTrainingCatalog)
async def get_fill_training_catalog(
    db: DbSession,
    user: CurrentUser,
) -> SubjectTrainingCatalog:
    del user
    return await fill_blank_training.get_fill_catalog(db)


@router.post(
    "/fill",
    response_model=TrainingSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_fill_training(
    data: SubjectTrainingCreate,
    db: DbSession,
    user: CurrentUser,
) -> TrainingSessionRead:
    session = await fill_blank_training.create_fill_training(db, user.id, data)
    return await session_response(db, session)


@router.get("/subject/catalog", response_model=SubjectTrainingCatalog)
async def get_subject_training_catalog(
    db: DbSession,
    user: CurrentUser,
) -> SubjectTrainingCatalog:
    del user
    return await subject_training.get_catalog(db)


async def session_response(db: DbSession, session) -> TrainingSessionRead:
    count = await service.completed_count(db, session.user_id, session.id)
    return TrainingSessionRead(
        id=session.id,
        training_type=session.training_type,
        title=session.title,
        status=session.status,
        total_questions=session.total_questions,
        completed_questions=count,
        subject=session.subject,
        chapter=session.chapter,
        knowledge_point=session.knowledge_point,
        scheduled_date=session.scheduled_date,
        plan_day=session.plan_day,
        selection_version=session.selection_version,
        selection_config=session.selection_config,
        started_at=session.started_at,
        completed_at=session.completed_at,
        created_at=session.created_at,
        items=[TrainingSessionItemRead.model_validate(item) for item in session.items],
    )


@router.post(
    "/subject",
    response_model=TrainingSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_subject_training(
    data: SubjectTrainingCreate,
    db: DbSession,
    user: CurrentUser,
) -> TrainingSessionRead:
    session = await subject_training.create_subject_training(db, user.id, data)
    return await session_response(db, session)


@router.get("", response_model=Page[TrainingSessionSummary])
async def list_training_sessions(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[TrainingSessionSummary]:
    sessions, total = await service.list_sessions(db, user.id, page, page_size)
    counts = await service.completed_counts(db, user.id, [session.id for session in sessions])
    items = [
        TrainingSessionSummary(
            id=session.id,
            training_type=session.training_type,
            title=session.title,
            status=session.status,
            total_questions=session.total_questions,
            completed_questions=counts.get(session.id, 0),
            subject=session.subject,
            created_at=session.created_at,
            completed_at=session.completed_at,
        )
        for session in sessions
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{session_id}", response_model=TrainingSessionRead)
async def get_training_session(
    session_id: int, db: DbSession, user: CurrentUser
) -> TrainingSessionRead:
    session = await service.get_session(db, user.id, session_id)
    return await session_response(db, session)


@router.get("/{session_id}/answers", response_model=list[AnswerResult])
async def get_training_answers(
    session_id: int, db: DbSession, user: CurrentUser
) -> list[AnswerResult]:
    rows = await service.list_session_answers(db, user.id, session_id)
    return [
        AnswerResult(
            **StudentAnswerRead.model_validate(answer).model_dump(),
            correct_answer=question.correct_answer,
            explanation=question.explanation,
        )
        for answer, question in rows
    ]


@router.post("/{session_id}/complete", response_model=TrainingSessionRead)
async def complete_training_session(
    session_id: int, db: DbSession, user: CurrentUser
) -> TrainingSessionRead:
    session = await service.complete_session(db, user.id, session_id)
    return await session_response(db, session)


@item_router.post(
    "/{item_id}/answer",
    response_model=AnswerResult,
    status_code=status.HTTP_201_CREATED,
)
async def submit_training_answer(
    item_id: int,
    data: TrainingAnswerSubmit,
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> AnswerResult:
    answer, question, created = await service.submit_item_answer(db, user.id, item_id, data)
    if created and not answer.is_correct:
        background_tasks.add_task(ai_analysis.analyze_answer_background, answer.id)
    return AnswerResult(
        **StudentAnswerRead.model_validate(answer).model_dump(),
        correct_answer=question.correct_answer,
        explanation=question.explanation,
    )
