"""add_github_pr_comments

Revision ID: 003_add_github_pr_comments
Revises: 002_add_quality_columns
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_github_pr_comments'
down_revision: Union[str, None] = '002_add_quality_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'github_pr_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('github_comment_id', sa.BigInteger(), nullable=True),
        sa.Column('commit_sha', sa.String(), nullable=True),
        sa.Column('comment_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repo_id', 'pr_number', name='uq_github_pr_comments_repo_pr')
    )
    op.create_index(op.f('ix_github_pr_comments_repo_id'), 'github_pr_comments', ['repo_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_github_pr_comments_repo_id'), table_name='github_pr_comments')
    op.drop_table('github_pr_comments')
