"""Add PR inventory fields

Revision ID: da37ed971326
Revises: 0115e9d4dc0d
Create Date: 2026-09-10 12:51:43.280053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da37ed971326'
down_revision: Union[str, Sequence[str], None] = '0115e9d4dc0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('purchase_requisitions', sa.Column('is_inventory_allocation', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('purchase_requisitions', sa.Column('allocated_asset_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_pr_allocated_asset', 'purchase_requisitions', 'assets', ['allocated_asset_id'], ['asset_id'], ondelete='SET NULL')
    op.alter_column('pr_items', 'unit_price', existing_type=sa.Numeric(15, 2), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('pr_items', 'unit_price', existing_type=sa.Numeric(15, 2), nullable=False)
    op.drop_constraint('fk_pr_allocated_asset', 'purchase_requisitions', type_='foreignkey')
    op.drop_column('purchase_requisitions', 'allocated_asset_id')
    op.drop_column('purchase_requisitions', 'is_inventory_allocation')
