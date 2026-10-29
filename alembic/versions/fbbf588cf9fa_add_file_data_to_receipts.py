"""add file_data to receipts

Revision ID: fbbf588cf9fa
Revises: 783291c81ba3
Create Date: 2026-10-05 15:47:16.133715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbbf588cf9fa'
down_revision: Union[str, Sequence[str], None] = '783291c81ba3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('receipts', sa.Column('file_data', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('receipts', 'file_data')
