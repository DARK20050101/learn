from datetime import date

from sqlalchemy.exc import IntegrityError

from app.models.daily_task import DailyTask
from app.models.question import Question, QuestionType
from app.services.daily_task_generator import (
    DailyTaskGenerator,
    SubjectPerformance,
    choose_questions,
)


def make_question(
    question_id: int,
    subject: str,
    difficulty: int = 2,
    point: str = "基础",
    tags: list[str] | None = None,
) -> Question:
    return Question(
        id=question_id,
        title=f"{subject}-{question_id}",
        content=f"题目 {question_id}",
        subject=subject,
        chapter="测试",
        question_type=QuestionType.single_choice,
        options=["A", "B"],
        correct_answer="A",
        explanation="解析",
        difficulty=difficulty,
        knowledge_points=[point],
        tags=tags or [],
        is_active=True,
    )


def test_default_distribution_is_three_two_one() -> None:
    candidates = [
        *[make_question(index, "英语") for index in range(1, 6)],
        *[make_question(index, "物理") for index in range(10, 14)],
        *[make_question(index, "数学") for index in range(20, 24)],
    ]

    result = choose_questions(candidates, {}, {}, set())
    subjects = [item.question.subject for item in result]

    assert subjects.count("英语") == 3
    assert subjects.count("物理") == 2
    assert subjects.count("数学") == 1
    assert len({item.question.id for item in result}) == 6


def test_insufficient_subject_is_filled_by_priority_order() -> None:
    candidates = [
        make_question(1, "英语"),
        make_question(2, "物理"),
        make_question(3, "数学"),
        make_question(4, "化学"),
        make_question(5, "化学"),
        make_question(6, "生物"),
    ]

    result = choose_questions(candidates, {}, {}, set())

    assert len(result) == 6
    assert {item.question.id for item in result} == {1, 2, 3, 4, 5, 6}


def test_low_mastery_knowledge_point_is_ranked_first() -> None:
    weak = make_question(1, "英语", point="定语从句")
    stable = make_question(2, "英语", point="基础词汇")
    candidates = [
        weak,
        stable,
        make_question(3, "英语"),
        make_question(4, "物理"),
        make_question(5, "物理"),
        make_question(6, "数学"),
    ]
    mastery = {("英语", "定语从句"): 20, ("英语", "基础词汇"): 80}

    result = choose_questions(candidates, {}, mastery, set())

    assert result[0].question.id == weak.id


def test_recent_wrong_point_gets_priority() -> None:
    wrong_point = make_question(1, "英语", point="时态")
    other = make_question(2, "英语", point="词汇")
    candidates = [
        wrong_point,
        other,
        make_question(3, "英语"),
        make_question(4, "物理"),
        make_question(5, "物理"),
        make_question(6, "数学"),
    ]

    result = choose_questions(candidates, {}, {}, {("英语", "时态")})

    assert result[0].question.id == wrong_point.id


def test_many_errors_lower_difficulty_and_streak_raises_it() -> None:
    english = [make_question(level, "英语", difficulty=level) for level in range(1, 5)]
    fillers = [make_question(10, "物理"), make_question(11, "物理"), make_question(12, "数学")]

    struggling = choose_questions(
        english + fillers,
        {"英语": SubjectPerformance(error_rate=0.75)},
        {},
        set(),
    )
    improving = choose_questions(
        english + fillers,
        {"英语": SubjectPerformance(error_rate=0.1, consecutive_correct=3)},
        {},
        set(),
    )

    assert struggling[0].question.difficulty in {1, 2}
    assert improving[0].question.difficulty in {3, 4}


class ScalarRows:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def __iter__(self):
        return iter(self.values)


class HistoryRows:
    def all(self) -> list[tuple[str, bool, list[str]]]:
        return []


class ConcurrentFakeSession:
    def __init__(self, existing: DailyTask, candidates: list[Question]) -> None:
        self.existing = existing
        self.candidates = candidates
        self.scalar_calls = 0
        self.scalars_calls = 0
        self.rolled_back = False

    async def scalar(self, _query: object):
        self.scalar_calls += 1
        if self.scalar_calls == 1:
            return None
        if self.scalar_calls == 2:
            return 0
        return self.existing

    async def scalars(self, _query: object) -> ScalarRows:
        self.scalars_calls += 1
        if self.scalars_calls == 1:
            return ScalarRows([])
        if self.scalars_calls == 2:
            return ScalarRows(self.candidates)
        return ScalarRows([])

    async def execute(self, _query: object) -> HistoryRows:
        return HistoryRows()

    def add(self, _value: object) -> None:
        pass

    async def commit(self) -> None:
        raise IntegrityError("insert", {}, Exception("unique conflict"))

    async def rollback(self) -> None:
        self.rolled_back = True


async def test_concurrent_unique_conflict_returns_created_task() -> None:
    candidates = [
        *[make_question(index, "英语") for index in range(1, 4)],
        *[make_question(index, "物理") for index in range(4, 6)],
        make_question(6, "数学"),
    ]
    existing = DailyTask(id=99, user_id=1, task_date=date.today(), day_number=1)
    db = ConcurrentFakeSession(existing, candidates)

    result = await DailyTaskGenerator().get_or_create_today(db, 1)  # type: ignore[arg-type]

    assert result is existing
    assert db.rolled_back


def test_fewer_than_six_candidates_stays_incomplete() -> None:
    result = choose_questions(
        [make_question(index, "英语") for index in range(1, 6)],
        {},
        {},
        set(),
    )
    assert len(result) == 5


def test_daily_task_prefers_distinct_material_groups() -> None:
    candidates = [
        make_question(1, "英语", tags=["material-group:reading-a"]),
        make_question(2, "英语", tags=["material-group:reading-a"]),
        make_question(3, "英语", tags=["material-group:reading-b"]),
        make_question(4, "英语", tags=["material-group:reading-c"]),
        make_question(5, "物理", tags=["material-group:physics-a"]),
        make_question(6, "物理", tags=["material-group:physics-b"]),
        make_question(7, "数学", tags=["material-group:math-a"]),
    ]

    result = choose_questions(candidates, {}, {}, set())
    groups = [
        next(tag for tag in item.question.tags if tag.startswith("material-group:"))
        for item in result
    ]

    assert len(result) == 6
    assert len(groups) == len(set(groups))
