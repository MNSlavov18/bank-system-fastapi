"""add is_accepted to credit_types

Revision ID: df36c4e1f872
Revises: 8c705667f479
Create Date: 2026-06-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df36c4e1f872'
down_revision: Union[str, Sequence[str], None] = '8c705667f479'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('credit_types', sa.Column('is_accepted', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    op.alter_column('credit_types', 'is_accepted', server_default=None)


def downgrade() -> None:
    op.drop_column('credit_types', 'is_accepted')
