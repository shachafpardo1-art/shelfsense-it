from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.main import app


def test_health_returns_healthy(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_returns_ready_with_working_database(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_returns_503_when_database_is_unavailable() -> None:
    class FailingSession:
        def execute(self, *args, **kwargs) -> None:
            raise SQLAlchemyError("boom")

    def override_get_db() -> Generator[FailingSession, None, None]:
        yield FailingSession()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}

    app.dependency_overrides.clear()
