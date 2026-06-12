"""add_simhash_value_to_knowledge_articles

Revision ID: a1b2c3d4e5f6
Revises: 725fc7ff1f4b
Create Date: 2026-06-12 10:30:00.000000+03:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '725fc7ff1f4b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'knowledge_articles',
        sa.Column('simhash_value', sa.BigInteger(), nullable=True, comment='SimHash fingerprint for de-duplication'),
    )
    op.create_index(
        op.f('ix_knowledge_articles_simhash_value'),
        'knowledge_articles',
        ['simhash_value'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_knowledge_articles_simhash_value'), table_name='knowledge_articles')
    op.drop_column('knowledge_articles', 'simhash_value')
