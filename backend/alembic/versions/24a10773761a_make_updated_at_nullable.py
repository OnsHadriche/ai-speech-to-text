"""make updated_at nullable

Revision ID: 24a10773761a
Revises: 2fb5daf384c3
Create Date: 2026-11-09 12:23:17.858055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24a10773761a'
down_revision: Union[str, Sequence[str], None] = '2fb5daf384c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "jobs",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=True,
        existing_nullable=False,
    )


def downgrade() -> None:
    # Populate NULL values before restoring NOT NULL.
    op.execute(
        "UPDATE jobs SET updated_at = created_at WHERE updated_at IS NULL"
    )

    op.alter_column(
        "jobs",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("CURRENT_TIMESTAMP"),
        nullable=False,
        existing_nullable=True,
    )
