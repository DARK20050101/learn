from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.learning_report import LearningReportRead
from app.services import learning_reports

router = APIRouter(prefix="/learning-report", tags=["学习报告"])


@router.get("", response_model=LearningReportRead)
async def get_learning_report(db: DbSession, user: CurrentUser) -> LearningReportRead:
    return await learning_reports.get_report(db, user.id)
