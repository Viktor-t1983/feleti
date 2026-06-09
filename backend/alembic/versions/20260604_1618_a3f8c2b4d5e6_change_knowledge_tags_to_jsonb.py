"""change_knowledge_tags_to_jsonb

Revision ID: a3f8c2b4d5e6
Revises: 47b2c1d3e9a0
Create Date: 2026-06-04 16:18:00.000000+03:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'a3f8c2b4d5e6'
down_revision = '47b2c1d3e9a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('knowledge_articles', 'tags',
                    type_=JSONB,
                    postgresql_using='tags::jsonb',
                    existing_nullable=False,
                    existing_server_default=sa.text("'[]'::json"),
    )


def downgrade() -> None:
    op.alter_column('knowledge_articles', 'tags',
                    type_=sa.JSON,
                    postgresql_using='tags::json',
                    existing_nullable=False,
                    existing_server_default=sa.text("'[]'::json"),
    )
