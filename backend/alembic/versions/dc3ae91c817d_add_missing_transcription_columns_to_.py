"""add missing transcription columns to jobs

Revision ID: dc3ae91c817d
Revises: 8d97c7ee409f
Create Date: 2026-11-11 11:09:45.139891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc3ae91c817d'
down_revision: Union[str, Sequence[str], None] = '8d97c7ee409f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("transcript_text", sa.Text(), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("detected_language", sa.String(length=10), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("language_probability", sa.Float(), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("transcription_segments", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "transcription_segments")
    op.drop_column("jobs", "language_probability")
    op.drop_column("jobs", "detected_language")
    op.drop_column("jobs", "transcript_text")