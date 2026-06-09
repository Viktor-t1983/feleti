"""add_article_analyses

Revision ID: b7c4d1e2f3a6
Revises: a3f8c2b4d5e6
Create Date: 2026-06-04 18:00:00.000000+03:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'b7c4d1e2f3a6'
down_revision = 'a3f8c2b4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('article_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('products', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('technologies', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('problems', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('equipment', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('key_insights', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('competitor_mentions', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('target_markets', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('ai_category', sa.String(length=100), nullable=True),
        sa.Column('raw_response', JSONB(), nullable=True),
        sa.Column('model_used', sa.String(length=200), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'DONE', 'ERROR', name='analysis_status'), nullable=False, server_default='PENDING'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['knowledge_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id'),
    )
    op.create_index('ix_article_analyses_article_id', 'article_analyses', ['article_id'])


def downgrade() -> None:
    op.drop_table('article_analyses')
    op.execute('DROP TYPE IF EXISTS analysis_status')
