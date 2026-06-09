"""add_topic_path_to_article_analyses

Revision ID: c8d5e2f3a4b7
Revises: b7c4d1e2f3a6
Create Date: 2026-06-05 13:55:00.000000+03:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d5e2f3a4b7'
down_revision = 'b7c4d1e2f3a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('article_analyses',
        sa.Column('topic_path', sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('article_analyses', 'topic_path')
