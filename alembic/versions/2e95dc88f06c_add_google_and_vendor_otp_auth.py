"""add_google_and_vendor_otp_auth

Revision ID: 2e95dc88f06c
Revises: phase6_platform_services
Create Date: 2026-08-04 22:19:35.579829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e95dc88f06c'
down_revision: Union[str, Sequence[str], None] = 'phase6_platform_services'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add new columns to users table
    op.add_column('users', sa.Column('google_id', sa.String(), nullable=True, comment='Google OAuth sub ID'))
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True, comment='User profile photo URL'))
    op.add_column('users', sa.Column('login_provider', sa.String(), nullable=True, server_default='LOCAL', comment='Auth provider (GOOGLE, LOCAL)'))
    op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])

    # 2. Create vendor_users table
    op.create_table(
        'vendor_users',
        sa.Column('vendor_user_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='Primary key for vendor user mapping'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='FK referencing user'),
        sa.Column('vendor_id', sa.BigInteger(), nullable=False, comment='FK referencing vendor'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('vendor_user_id')
    )

    # 3. Create otp_requests table
    op.create_table(
        'otp_requests',
        sa.Column('request_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='Primary key for OTP request'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='Vendor email address requesting OTP'),
        sa.Column('otp_hash', sa.String(length=255), nullable=False, comment='Securely hashed OTP code'),
        sa.Column('attempts', sa.BigInteger(), nullable=False, server_default='0', comment='Verification retry count'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='OTP expiration timestamp'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='Timestamp when OTP was generated'),
        sa.PrimaryKeyConstraint('request_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('otp_requests')
    op.drop_table('vendor_users')
    op.drop_constraint('uq_users_google_id', 'users', type_='unique')
    op.drop_column('users', 'login_provider')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'google_id')
