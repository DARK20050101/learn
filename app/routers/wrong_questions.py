from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import Page
from app.schemas.training_session import TrainingSessionItemRead, TrainingSessionRead
from app.schemas.wrong_question import WrongQuestionRead, WrongQuestionSort
from app.services import wrong_questions as service
from app.services.training_sessions import completed_count

router = APIRouter(prefix="/wrong-questions", tags=["错题本"])


@router.get("", response_model=Page[WrongQuestionRead])
async def list_wrong_questions(
    db: DbSession,
    user: CurrentUser,
    subject: str | None = Query(default=None, min_length=1, max_length=50),
    knowledge_point_code: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    sort: WrongQuestionSort = WrongQuestionSort.error_count_desc,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[WrongQuestionRead]:
    items, total = await service.list_wrong_questions(
        db,
        user.id,
        subject=subject,
        knowledge_point_code=knowledge_point_code,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("/{question_id}/practice", response_model=TrainingSessionRead)
async def practice_wrong_question(
    question_id: int,
    db: DbSession,
    user: CurrentUser,
) -> TrainingSessionRead:
    session = await service.create_wrong_review(db, user.id, question_id)
    count = await completed_count(db, user.id, session.id)
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
