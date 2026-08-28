"""Unit tests for stateful authentication and self-service identity workflows."""

from uuid import UUID, uuid4

import pytest
from app.api.deps import require_role
from app.core.config import Settings
from app.core.exceptions import RiskGuardError
from app.core.security import create_token, hash_password
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.db.types import UserRole
from app.schemas.auth import LoginRequest, UpdateCurrentUserRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService


class FakeSession:
    """Minimal in-memory async session used to test service policy, not SQLAlchemy itself."""

    def __init__(self) -> None:
        self.added: list[object] = []
        self.executed = False
        self.deleted: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        return None

    async def execute(self, statement: object) -> None:
        self.executed = statement is not None

    async def delete(self, value: object) -> None:
        self.deleted.append(value)


class FakeUsers:
    def __init__(self, user: User, token: RefreshToken | None = None) -> None:
        self.user = user
        self.token = token

    async def by_email(self, email: str) -> User | None:
        return self.user if email == self.user.email else None

    async def by_id(self, user_id: UUID) -> User | None:
        return self.user if user_id == self.user.id else None

    async def refresh_token(self, token_id: UUID) -> RefreshToken | None:
        if self.token is not None and self.token.jti == str(token_id):
            return self.token
        return None


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test", jwt_secret="a-test-secret-that-is-longer-than-32-chars")


@pytest.fixture
def user() -> User:
    return User(
        id=uuid4(),
        email="citizen@example.com",
        password_hash=hash_password("Valid-password-123!"),
        full_name="Citizen",
        role=UserRole.CITIZEN,
        is_active=True,
    )


async def test_login_rejects_inactive_user(settings: Settings, user: User) -> None:
    user.is_active = False
    service = AuthService(FakeSession(), settings)  # type: ignore[arg-type]
    service._users = FakeUsers(user)  # type: ignore[assignment]

    with pytest.raises(RiskGuardError, match="invalid"):
        await service.login(LoginRequest(email=user.email, password="Valid-password-123!"))


async def test_refresh_rotation_and_logout_revoke_server_state(
    settings: Settings, user: User
) -> None:
    refresh, refresh_id, expiry = create_token(user.id, "refresh", settings)
    record = RefreshToken(user_id=user.id, jti=str(refresh_id), expires_at=expiry)
    session = FakeSession()
    service = AuthService(session, settings)  # type: ignore[arg-type]
    service._users = FakeUsers(user, record)  # type: ignore[assignment]

    tokens = await service.refresh(refresh)

    assert record.revoked_at is not None
    assert tokens.access_token != tokens.refresh_token
    new_record = next(item for item in session.added if isinstance(item, RefreshToken))
    service._users = FakeUsers(user, new_record)  # type: ignore[assignment]
    await service.logout(tokens.refresh_token)
    assert new_record.revoked_at is not None


async def test_user_update_and_deletion_are_explicit(user: User) -> None:
    session = FakeSession()
    service = UserService(session)  # type: ignore[arg-type]
    updated = await service.update_current_user(
        user,
        UpdateCurrentUserRequest(full_name="Updated Citizen", new_password="Changed-password-123!"),
    )
    assert updated.full_name == "Updated Citizen"
    assert updated.password_hash != "Changed-password-123!"

    await service.delete_current_user(user)
    assert session.executed
    assert session.deleted == [user]


async def test_singular_role_dependency_enforces_rbac(user: User) -> None:
    citizen_only = require_role(UserRole.CITIZEN)
    assert await citizen_only(user) is user

    responder_only = require_role(UserRole.RESPONDER)
    with pytest.raises(RiskGuardError, match="permission"):
        await responder_only(user)
