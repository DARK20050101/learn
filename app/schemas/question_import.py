from typing import Any, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.question import QuestionType
from app.models.question_import import ImportStatus
from app.schemas.question import AnswerValue


class QuestionImportItem(BaseModel):
    subject: str = Field(min_length=1, max_length=50)
    chapter: str = Field(min_length=1, max_length=100)
    knowledge_points: list[str] = Field(min_length=1)
    difficulty: int = Field(ge=1, le=5)
    type: QuestionType
    question: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)
    answer: AnswerValue
    solution: str = Field(min_length=1)
    source: str = Field(default="", max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    tags: list[str] = Field(default_factory=list)

    @field_validator("subject", "chapter", "question", "solution", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("knowledge_points")
    @classmethod
    def normalize_knowledge_points(cls, values: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not cleaned:
            raise ValueError("knowledge_points 至少包含一个非空知识点")
        return cleaned

    @model_validator(mode="after")
    def validate_and_normalize_answer(self) -> Self:
        if self.type in {QuestionType.single_choice, QuestionType.multiple_choice}:
            if len(self.options) < 2:
                raise ValueError("选择题至少需要两个选项")
            self.options = [option.strip() for option in self.options]
            if any(not option for option in self.options):
                raise ValueError("选项不能为空")
            if len(set(self.options)) != len(self.options):
                raise ValueError("选项不能重复")
            if self.type == QuestionType.single_choice:
                if not isinstance(self.answer, str):
                    raise ValueError("单选题 answer 必须是字符串")
                self.answer = self._resolve_option(self.answer)
            else:
                if not isinstance(self.answer, list) or not self.answer:
                    raise ValueError("多选题 answer 必须是非空字符串数组")
                self.answer = [self._resolve_option(value) for value in self.answer]
                if len(set(self.answer)) != len(self.answer):
                    raise ValueError("多选题答案不能重复")
        elif self.type == QuestionType.true_false:
            if not isinstance(self.answer, bool):
                raise ValueError("判断题 answer 必须是布尔值")
            if self.options:
                raise ValueError("判断题不需要 options")
        elif self.type == QuestionType.short_answer:
            if not isinstance(self.answer, str) or not self.answer.strip():
                raise ValueError("简答题 answer 必须是非空字符串")
            self.answer = self.answer.strip()
            if self.options:
                raise ValueError("简答题不需要 options")
        elif self.type == QuestionType.fill_blank:
            raw = self.answer if isinstance(self.answer, list) else [self.answer]
            if not all(isinstance(value, str) for value in raw):
                raise ValueError("填空题 answer 必须是字符串或字符串数组")
            accepted = list(
                dict.fromkeys(value.strip() for value in raw if value.strip())
            )
            if not accepted:
                raise ValueError("填空题至少需要一个可接受答案")
            self.answer = accepted
            if self.options:
                raise ValueError("填空题不需要 options")
        return self

    def _resolve_option(self, answer: str) -> str:
        value = answer.strip()
        if value in self.options:
            return value
        if len(value) == 1 and "A" <= value.upper() <= "Z":
            index = ord(value.upper()) - ord("A")
            if index < len(self.options):
                return self.options[index]
        raise ValueError(f"答案 {answer!r} 不在 options 中")

    def as_question_values(self, content_hash: str) -> dict[str, Any]:
        return {
            "title": self.title or f"{self.chapter} · {self.knowledge_points[0]}",
            "content": self.question,
            "subject": self.subject,
            "chapter": self.chapter,
            "question_type": self.type,
            "options": self.options or None,
            "correct_answer": self.answer,
            "explanation": self.solution,
            "difficulty": self.difficulty,
            "knowledge_points": self.knowledge_points,
            "tags": self.tags,
            "source": self.source or None,
            "content_hash": content_hash,
            "is_active": True,
        }


class ImportErrorDetail(BaseModel):
    index: int
    question: str | None = None
    errors: list[str]


class QuestionImportResult(BaseModel):
    batch_id: int
    filename: str
    status: ImportStatus
    total_count: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    errors: list[ImportErrorDetail]
