from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_status import KnowledgeStatus


async def list_statuses(db: AsyncSession, user_id: int) -> list[KnowledgeStatus]:
    rows = await db.scalars(
        select(KnowledgeStatus)
        .where(KnowledgeStatus.user_id == user_id)
        .order_by(KnowledgeStatus.mastery_score, KnowledgeStatus.knowledge_point)
    )
    return list(rows)
