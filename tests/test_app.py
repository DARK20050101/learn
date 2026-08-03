from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_contains_core_modules() -> None:
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    assert "/api/v1/users/register" in paths
    assert "/api/v1/questions" in paths
    assert "/api/v1/student-answers" in paths
    assert "/api/v1/daily-tasks/today" in paths
    assert "/api/v1/daily-tasks/today/refresh" in paths
    assert "/api/v1/learning-report" in paths
    assert "/api/v1/knowledge-status" in paths
    assert "/api/v1/student-answers/{answer_id}/analysis" in paths
    assert "/api/v1/student-answers/{answer_id}/feedback" in paths
    assert "/api/v1/training-sessions/{session_id}" in paths
    assert "/api/v1/training-sessions/{session_id}/answers" in paths
    assert "/api/v1/training-session-items/{item_id}/answer" in paths
    assert "/api/v1/training-sessions/subject/catalog" in paths
    assert "/api/v1/training-sessions/subject" in paths
    assert "/api/v1/training-sessions/fill/catalog" in paths
    assert "/api/v1/training-sessions/fill" in paths
    assert "/api/v1/wrong-questions" in paths
    assert "/api/v1/wrong-questions/{question_id}/practice" in paths
    assert "/api/v1/ai-analysis" not in paths
