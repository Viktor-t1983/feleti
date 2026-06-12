"""add_source_reputation

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-12 11:00:00.000000+03:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'source_reputation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('domain', sa.String(length=300), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('is_blacklisted', sa.Boolean(), nullable=False),
        sa.Column('label', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain'),
    )
    op.create_index(op.f('ix_source_reputation_domain'), 'source_reputation', ['domain'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_source_reputation_domain'), table_name='source_reputation')
    op.drop_table('source_reputation')
