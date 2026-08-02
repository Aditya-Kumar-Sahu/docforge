"""add_quality_columns

Revision ID: 002_add_quality_columns
Revises: b3f4e2a9c01d
Create Date: 2026-08-02 22:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "002_add_quality_columns"
down_revision: Union[str, Sequence[str], None] = "b3f4e2a9c01d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("endpoints", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("endpoints", sa.Column("quality_dimensions", sa.JSON(), nullable=True))
    op.add_column("endpoints", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("endpoints", sa.Column("needs_human_review", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("endpoints", sa.Column("source_code_snippet", sa.Text(), nullable=True))
    
    # Remove server defaults after backfilling
    op.alter_column("endpoints", "attempts", server_default=None)
    op.alter_column("endpoints", "needs_human_review", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("endpoints", "source_code_snippet")
    op.drop_column("endpoints", "needs_human_review")
    op.drop_column("endpoints", "attempts")
    op.drop_column("endpoints", "quality_dimensions")
    op.drop_column("endpoints", "quality_score")
