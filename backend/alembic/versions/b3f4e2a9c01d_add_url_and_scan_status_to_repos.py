"""add_url_and_scan_status_to_repos

Revision ID: b3f4e2a9c01d
Revises: 418bdf627f58
Create Date: 2026-07-24 16:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b3f4e2a9c01d"
down_revision: Union[str, Sequence[str], None] = "418bdf627f58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("repos", sa.Column("url", sa.String(), nullable=False, server_default=""))
    op.add_column(
        "repos",
        sa.Column("scan_status", sa.String(), nullable=False, server_default="pending"),
    )
    # Remove server defaults after backfilling so future rows use app-level defaults
    op.alter_column("repos", "url", server_default=None)
    op.alter_column("repos", "scan_status", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("repos", "scan_status")
    op.drop_column("repos", "url")
