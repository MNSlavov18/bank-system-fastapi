"""add failed credits table and remove is_accepted from credit_types

Revision ID: d3f8c7b2a590
Revises: 9afadee42c93
Create Date: 2026-06-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3f8c7b2a590'
down_revision: Union[str, Sequence[str], None] = '9afadee42c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'failed_credits',
        sa.Column('failed_credit_id', sa.Integer(), nullable=False),
        sa.Column('type_name', sa.Enum('CONSUMER', 'MORTGAGE', name='credittypename'), nullable=False),
        sa.Column('requested_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('requested_term_months', sa.Integer(), nullable=False),
        sa.Column('failure_reason', sa.String(length=255), nullable=False),
        sa.Column('failed_at', sa.Date(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.CheckConstraint('requested_amount > 0', name='check_failed_requested_amount_positive'),
        sa.CheckConstraint('requested_term_months > 0', name='check_failed_requested_term_positive'),
        sa.ForeignKeyConstraint(['account_id'], ['bank_accounts.account_id']),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id']),
        sa.PrimaryKeyConstraint('failed_credit_id')
    )
    op.create_index(op.f('ix_failed_credits_failed_credit_id'), 'failed_credits', ['failed_credit_id'], unique=False)

    op.drop_column('credit_types', 'is_accepted')


def downgrade() -> None:
    op.add_column('credit_types', sa.Column('is_accepted', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    op.alter_column('credit_types', 'is_accepted', server_default=None)

    op.drop_index(op.f('ix_failed_credits_failed_credit_id'), table_name='failed_credits')
    op.drop_table('failed_credits')
