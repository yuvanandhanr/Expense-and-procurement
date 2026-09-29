"""make legacy asset columns nullable

Revision ID: 783291c81ba3
Revises: 20260928_employee_type
Create Date: 2026-09-30 00:37:45.953796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '783291c81ba3'
down_revision: Union[str, Sequence[str], None] = '20260928_employee_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('assets', 'category', existing_type=sa.String(), nullable=True)
    op.alter_column('assets', 'asset_name', existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('assets', 'category', existing_type=sa.String(), nullable=False)
    op.alter_column('assets', 'asset_name', existing_type=sa.String(), nullable=False)
