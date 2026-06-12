"""add_entity_links

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-12 12:00:00.000000+03:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'entity_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('relation', sa.String(50), nullable=False, server_default='mentions'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_type', 'source_id', 'target_type', 'target_id', 'relation',
                            name='uq_entity_link'),
    )
    op.create_index(op.f('ix_entity_links_source_type_source_id'), 'entity_links',
                    ['source_type', 'source_id'], unique=False)
    op.create_index(op.f('ix_entity_links_target_type_target_id'), 'entity_links',
                    ['target_type', 'target_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_entity_links_target_type_target_id'), table_name='entity_links')
    op.drop_index(op.f('ix_entity_links_source_type_source_id'), table_name='entity_links')
    op.drop_table('entity_links')
