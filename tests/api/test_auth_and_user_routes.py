"""Route-level tests using dependency overrides rather than a real database."""

from uuid import uuid4

from app.api.deps import get_current_user
from app.api.v1.auth import auth_service
from app.core.config import Settings
from app.db.models.user import User
from app.db.session import get_db_session
from app.db.types import UserRole
from app.main import create_application
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from fastapi.testclient import TestClient


class FakeSession:
    async def flush(self) -> None:
        return None

    async def execute(self, statement: object) -> None:
        return None

    async def delete(self, value: object) -> None:
        return None


class StubAuthService:
    def __init__(self, user: User) -> None:
        self.user = user

    async def register(self, payload: RegisterRequest) -> User:
        return self.user

    async def login(self, payload: LoginRequest) -> TokenResponse:
        return TokenResponse(access_token="access", refresh_token="refresh", expires_in=900)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        return TokenResponse(
            access_token="rotated-access", refresh_token="rotated-refresh", expires_in=900
        )

    async def logout(self, refresh_token: str) -> None:
        return None


def test_auth_and_current_user_routes_are_wired() -> None:
    user = User(
        id=uuid4(),
        email="citizen@example.com",
        password_hash="stored-hash",
        full_name="Citizen",
        role=UserRole.CITIZEN,
        is_active=True,
    )
    application = create_application(
        Settings(environment="test", jwt_secret="a-test-secret-that-is-longer-than-32-chars")
    )
    application.dependency_overrides[auth_service] = lambda: StubAuthService(user)
    application.dependency_overrides[get_current_user] = lambda: user
    application.dependency_overrides[get_db_session] = lambda: FakeSession()
    client = TestClient(application)

    assert (
        client.post(
            "/api/v1/auth/register",
            json={"email": user.email, "password": "Valid-password-123!", "full_name": "Citizen"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": user.email, "password": "password"}
        ).status_code
        == 200
    )
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": "refresh"}).status_code == 200
    assert client.post("/api/v1/auth/logout", json={"refresh_token": "refresh"}).status_code == 204
    assert client.get("/api/v1/users/me").status_code == 200
    assert (
        client.patch("/api/v1/users/me", json={"full_name": "Updated Citizen"}).status_code == 200
    )
    assert client.delete("/api/v1/users/me").status_code == 204

    application.dependency_overrides.clear()
