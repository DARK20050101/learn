from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject: str
    knowledge_point: str
    attempt_count: int
    correct_count: int
    mastery_score: float
    last_practiced_at: datetime | None
