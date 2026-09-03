"""merge heads

Revision ID: 629999ee2f2d
Revises: 20260901_expense_integrity, 8caa9487e7c8
Create Date: 2026-09-03 06:37:57.704244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '629999ee2f2d'
down_revision: Union[str, Sequence[str], None] = ('20260901_expense_integrity', '8caa9487e7c8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
