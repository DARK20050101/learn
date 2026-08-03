from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import QuestionType
from app.schemas.training_session import SubjectTrainingCatalog, SubjectTrainingCreate
from app.services import subject_training


async def get_fill_catalog(db: AsyncSession) -> SubjectTrainingCatalog:
    return await subject_training.get_catalog(db, question_type=QuestionType.fill_blank)


async def create_fill_training(
    db: AsyncSession,
    user_id: int,
    data: SubjectTrainingCreate,
):
    return await subject_training.create_subject_training(
        db,
        user_id,
        data,
        question_type=QuestionType.fill_blank,
    )
