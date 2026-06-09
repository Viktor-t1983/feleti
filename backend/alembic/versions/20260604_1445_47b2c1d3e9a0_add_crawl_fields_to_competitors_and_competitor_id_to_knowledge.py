"""add_crawl_fields_to_competitors_and_competitor_id_to_knowledge

Revision ID: 47b2c1d3e9a0
Revises: 0fe23cac1fd3
Create Date: 2026-06-04 14:45:00.000000+03:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47b2c1d3e9a0'
down_revision = '0fe23cac1fd3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('competitors', sa.Column('base_url', sa.String(500), nullable=True))
    op.add_column('competitors', sa.Column('sitemap_url', sa.String(500), nullable=True))
    op.add_column('competitors', sa.Column('crawl_config', sa.JSON(), nullable=True))
    op.add_column('competitors', sa.Column('crawl_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('competitors', sa.Column('crawl_error', sa.Text(), nullable=True))
    op.add_column('competitors', sa.Column('last_crawled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('competitors', sa.Column('articles_count', sa.Integer(), nullable=False, server_default='0'))

    op.add_column('knowledge_articles', sa.Column('competitor_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_knowledge_articles_competitor_id'), 'knowledge_articles', ['competitor_id'])
    op.create_foreign_key(
        'fk_knowledge_articles_competitor_id',
        'knowledge_articles', 'competitors',
        ['competitor_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_knowledge_articles_competitor_id', 'knowledge_articles', type_='foreignkey')
    op.drop_index(op.f('ix_knowledge_articles_competitor_id'), table_name='knowledge_articles')
    op.drop_column('knowledge_articles', 'competitor_id')

    op.drop_column('competitors', 'articles_count')
    op.drop_column('competitors', 'last_crawled_at')
    op.drop_column('competitors', 'crawl_error')
    op.drop_column('competitors', 'crawl_status')
    op.drop_column('competitors', 'crawl_config')
    op.drop_column('competitors', 'sitemap_url')
    op.drop_column('competitors', 'base_url')
