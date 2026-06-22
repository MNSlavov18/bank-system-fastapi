"""add loan disbursement and automatic payment

Revision ID: aea40a7a0850
Revises: d3f8c7b2a590
Create Date: 2026-06-22 11:38:11.214187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "aea40a7a0850"
down_revision: Union[str, Sequence[str], None] = "d3f8c7b2a590"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "loans",
        sa.Column(
            "disbursement_method",
            sa.Enum("CASH", "BANK_TRANSFER", name="loandisbursementmethod"),
            nullable=False,
            server_default="BANK_TRANSFER"
        )
    )

    op.add_column(
        "loans",
        sa.Column(
            "disbursement_account_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.add_column(
        "loans",
        sa.Column(
            "auto_payment_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0")
        )
    )

    op.add_column(
        "loans",
        sa.Column(
            "payment_account_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.create_foreign_key(
        "fk_loans_disbursement_account_id_bank_accounts",
        "loans",
        "bank_accounts",
        ["disbursement_account_id"],
        ["account_id"]
    )

    op.create_foreign_key(
        "fk_loans_payment_account_id_bank_accounts",
        "loans",
        "bank_accounts",
        ["payment_account_id"],
        ["account_id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_loans_payment_account_id_bank_accounts",
        "loans",
        type_="foreignkey"
    )

    op.drop_constraint(
        "fk_loans_disbursement_account_id_bank_accounts",
        "loans",
        type_="foreignkey"
    )

    op.drop_column("loans", "payment_account_id")
    op.drop_column("loans", "auto_payment_enabled")
    op.drop_column("loans", "disbursement_account_id")
    op.drop_column("loans", "disbursement_method")