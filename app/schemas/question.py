from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.question import QuestionType

AnswerValue = str | list[str] | bool


class QuestionBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=50)
    chapter: str | None = Field(default=None, max_length=100)
    question_type: QuestionType
    options: list[str] | None = None
    explanation: str | None = None
    source: str | None = Field(default=None, max_length=255)
    difficulty: int = Field(default=1, ge=1, le=5)
    knowledge_points: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class QuestionCreate(QuestionBase):
    correct_answer: AnswerValue

    @model_validator(mode="after")
    def validate_answer_shape(self) -> Self:
        if (
            self.question_type
            in {
                QuestionType.single_choice,
                QuestionType.multiple_choice,
            }
            and not self.options
        ):
            raise ValueError("选择题必须提供 options")
        if self.question_type == QuestionType.multiple_choice and not isinstance(
            self.correct_answer, list
        ):
            raise ValueError("多选题 correct_answer 必须是字符串数组")
        if self.question_type == QuestionType.true_false and not isinstance(
            self.correct_answer, bool
        ):
            raise ValueError("判断题 correct_answer 必须是布尔值")
        return self


class QuestionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1, max_length=50)
    chapter: str | None = Field(default=None, min_length=1, max_length=100)
    options: list[str] | None = None
    correct_answer: AnswerValue | None = None
    explanation: str | None = None
    source: str | None = Field(default=None, max_length=255)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    knowledge_points: list[str] | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class QuestionRead(QuestionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class QuestionAdminRead(QuestionRead):
    correct_answer: AnswerValue
