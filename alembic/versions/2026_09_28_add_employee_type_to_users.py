"""add employee_type to users

Revision ID: 20260928_employee_type
Revises: 
Create Date: 2026-09-28 17:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260928_employee_type'
down_revision = '5e6a9b4f9d1a'

def upgrade():
    # We use a try-except block or check if it exists so it doesn't fail if already added
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS employee_type VARCHAR(50) DEFAULT 'Full-Time'")

def downgrade():
    op.drop_column('users', 'employee_type')
