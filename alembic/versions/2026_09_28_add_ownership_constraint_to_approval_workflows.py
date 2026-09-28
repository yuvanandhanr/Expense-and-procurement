"""Add ownership fields and constraint to ApprovalWorkflow

Revision ID: 5e6a9b4f9d1a
Revises: 
Create Date: 2026-09-28 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e6a9b4f9d1a'
down_revision: Union[str, None] = 'da37ed971326'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns
    op.add_column('approval_workflows', sa.Column('claim_id', sa.BigInteger(), nullable=True))
    op.add_column('approval_workflows', sa.Column('po_id', sa.BigInteger(), nullable=True))
    op.add_column('approval_workflows', sa.Column('invoice_id', sa.BigInteger(), nullable=True))

    # Add foreign keys
    op.create_foreign_key('approval_workflows_claim_id_fkey', 'approval_workflows', 'expense_claims', ['claim_id'], ['claim_id'], ondelete='CASCADE')
    op.create_foreign_key('approval_workflows_po_id_fkey', 'approval_workflows', 'purchase_orders', ['po_id'], ['po_id'], ondelete='CASCADE')
    op.create_foreign_key('approval_workflows_invoice_id_fkey', 'approval_workflows', 'vendor_invoices', ['invoice_id'], ['invoice_id'], ondelete='CASCADE')

    # Add CHECK constraint
    op.create_check_constraint(
        'check_exclusive_workflow_ownership',
        'approval_workflows',
        "(claim_id IS NOT NULL)::int + (pr_id IS NOT NULL)::int + (po_id IS NOT NULL)::int + (invoice_id IS NOT NULL)::int = 1"
    )


def downgrade() -> None:
    op.drop_constraint('check_exclusive_workflow_ownership', 'approval_workflows', type_='check')
    op.drop_constraint('approval_workflows_invoice_id_fkey', 'approval_workflows', type_='foreignkey')
    op.drop_constraint('approval_workflows_po_id_fkey', 'approval_workflows', type_='foreignkey')
    op.drop_constraint('approval_workflows_claim_id_fkey', 'approval_workflows', type_='foreignkey')
    op.drop_column('approval_workflows', 'invoice_id')
    op.drop_column('approval_workflows', 'po_id')
    op.drop_column('approval_workflows', 'claim_id')
