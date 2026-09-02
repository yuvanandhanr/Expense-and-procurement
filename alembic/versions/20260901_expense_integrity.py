"""Enforce reimbursement descriptions and receipt-content uniqueness.

Revision ID: 20260901_expense_integrity
Revises: 0d67a7c3a17e
Create Date: 2026-09-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260901_expense_integrity"
down_revision: Union[str, Sequence[str], None] = "0d67a7c3a17e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing records predate the mandatory field. Preserve them without
    # inventing a business justification, while ensuring they no longer cause
    # response validation failures.
    op.execute(
        "UPDATE expense_reports "
        "SET justification = 'Legacy report: description unavailable' "
        "WHERE justification IS NULL OR trim(justification) = ''"
    )
    op.alter_column(
        "expense_reports", "justification", existing_type=sa.Text(), nullable=False
    )
    op.add_column("receipts", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.create_unique_constraint(
        "uq_receipt_report_content_hash", "receipts", ["expense_report_id", "content_hash"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_receipt_report_content_hash", "receipts", type_="unique")
    op.drop_column("receipts", "content_hash")
    op.alter_column(
        "expense_reports", "justification", existing_type=sa.Text(), nullable=True
    )
