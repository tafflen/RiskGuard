"""Add refresh-token server state for logout and rotation.

Revision ID: 20260827_0002
Revises: 20260826_0001
Create Date: 2026-08-27
"""

from alembic import op

revision = "20260827_0002"
down_revision = "20260826_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add opaque refresh-token identifiers without storing bearer credentials."""
    op.execute(
        """
        CREATE TABLE refresh_tokens (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            jti VARCHAR(36) NOT NULL UNIQUE,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id)")
    op.execute("CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens (expires_at)")


def downgrade() -> None:
    """Remove refresh token state."""
    op.execute("DROP TABLE refresh_tokens")
