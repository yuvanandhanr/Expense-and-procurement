"""add_enterprise_identity_and_organization_tables

Revision ID: 20260803_identity_org
Revises: None
Create Date: 2026-08-03 15:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260803_identity_org'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create designations table
    op.create_table(
        'designations',
        sa.Column('designation_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('designation_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('designation_id'),
        sa.UniqueConstraint('designation_name')
    )

    # Add columns to users table
    op.add_column('users', sa.Column('designation_id', sa.BigInteger(), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('is_locked', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.create_foreign_key('users_designation_id_fkey', 'users', 'designations', ['designation_id'], ['designation_id'], ondelete='SET NULL')

    # Create budget_codes table
    op.create_table(
        'budget_codes',
        sa.Column('budget_code_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('budget_code', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department_id', sa.BigInteger(), nullable=True),
        sa.Column('cost_center_id', sa.BigInteger(), nullable=True),
        sa.Column('annual_budget', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('available_budget', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('fiscal_year', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Active', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.department_id'], name='budget_codes_department_id_fkey', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cost_center_id'], ['cost_centres.cost_center_id'], name='budget_codes_cost_center_id_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('budget_code_id'),
        sa.UniqueConstraint('budget_code')
    )

    # Create organization_settings table
    op.create_table(
        'organization_settings',
        sa.Column('settings_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('org_name', sa.String(length=255), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=True),
        sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=True),
        sa.Column('fiscal_year_start', sa.Date(), nullable=True),
        sa.Column('fiscal_year_end', sa.Date(), nullable=True),
        sa.Column('approval_thresholds', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('password_policy', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('session_timeout_minutes', sa.Integer(), server_default='30', nullable=True),
        sa.Column('logo_url', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('settings_id')
    )

    # Create login_history table
    op.create_table(
        'login_history',
        sa.Column('history_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('login_time', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=1024), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Success', nullable=True),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name='login_history_user_id_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('history_id')
    )

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('token_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('is_expired', sa.Boolean(), server_default='false', nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name='refresh_tokens_user_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('token_id'),
        sa.UniqueConstraint('token')
    )


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('login_history')
    op.drop_table('organization_settings')
    op.drop_table('budget_codes')
    op.drop_constraint('users_designation_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'is_locked')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'designation_id')
    op.drop_table('designations')
