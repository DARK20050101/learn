from fastapi import APIRouter

from app.routers import (
    daily_tasks,
    knowledge_status,
    learning_reports,
    questions,
    student_answers,
    training_sessions,
    users,
    wrong_questions,
)

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(questions.router)
api_router.include_router(student_answers.router)
api_router.include_router(daily_tasks.router)
api_router.include_router(knowledge_status.router)
api_router.include_router(learning_reports.router)
api_router.include_router(training_sessions.router)
api_router.include_router(training_sessions.item_router)
api_router.include_router(wrong_questions.router)
