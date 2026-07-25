from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.knowledge_status import KnowledgeStatusRead
from app.services import knowledge_status as service

router = APIRouter(prefix="/knowledge-status", tags=["知识掌握"])


@router.get("", response_model=list[KnowledgeStatusRead])
async def list_statuses(db: DbSession, user: CurrentUser) -> list[KnowledgeStatusRead]:
    return await service.list_statuses(db, user.id)
