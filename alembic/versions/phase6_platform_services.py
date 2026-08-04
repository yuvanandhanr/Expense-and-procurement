"""add phase 6 platform services tables

Revision ID: phase6_platform_services
Revises: 0970733350dd
Create Date: 2026-08-04 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'phase6_platform_services'
down_revision: Union[str, Sequence[str], None] = '0970733350dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. notification_templates
    op.create_table(
        'notification_templates',
        sa.Column('template_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), unique=True, nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('template_id')
    )

    # 2. notifications
    op.create_table(
        'notifications',
        sa.Column('notification_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Unread', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('notification_id')
    )

    # 3. notification_preferences
    op.create_table(
        'notification_preferences',
        sa.Column('preference_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), unique=True, nullable=False),
        sa.Column('email_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('in_app_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('categories', sa.Text(), nullable=True), # Store comma separated or JSON string
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('preference_id')
    )

    # 4. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('audit_log_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.String(length=100), nullable=True),
        sa.Column('previous_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('audit_log_id')
    )

    # 5. activity_logs
    op.create_table(
        'activity_logs',
        sa.Column('activity_log_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('activity_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('record_id', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('activity_log_id')
    )

    # 6. reports
    op.create_table(
        'reports',
        sa.Column('report_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('report_id')
    )

    # 7. scheduled_reports
    op.create_table(
        'scheduled_reports',
        sa.Column('scheduled_report_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('frequency', sa.String(length=50), nullable=False),
        sa.Column('recipients', sa.Text(), nullable=False),
        sa.Column('format', sa.String(length=50), nullable=False),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('scheduled_report_id')
    )

    # 8. dashboard_widgets
    op.create_table(
        'dashboard_widgets',
        sa.Column('widget_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('widget_type', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('configuration', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('widget_id')
    )

    # 9. saved_filters
    op.create_table(
        'saved_filters',
        sa.Column('filter_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('filter_query', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('filter_id')
    )

    # 10. search_index
    op.create_table(
        'search_index',
        sa.Column('index_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('index_id')
    )

    # 11. attachments
    op.create_table(
        'attachments',
        sa.Column('attachment_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('attachment_id')
    )

    # 12. attachment_versions
    op.create_table(
        'attachment_versions',
        sa.Column('version_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('attachment_id', sa.BigInteger(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.attachment_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('version_id')
    )

    # 13. jobs
    op.create_table(
        'jobs',
        sa.Column('job_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('job_type', sa.String(length=100), nullable=False),
        sa.Column('frequency', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Idle', nullable=False),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('job_id')
    )

    # 14. job_history
    op.create_table(
        'job_history',
        sa.Column('history_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('job_id', sa.BigInteger(), nullable=False),
        sa.Column('run_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('history_id')
    )

    # 15. system_health
    op.create_table(
        'system_health',
        sa.Column('health_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('component', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('health_id')
    )

    # 16. system_metrics
    op.create_table(
        'system_metrics',
        sa.Column('metric_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('labels', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('metric_id')
    )

    # 17. system_settings
    op.create_table(
        'system_settings',
        sa.Column('setting_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), unique=True, nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), server_default='General', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('setting_id')
    )

    # 18. email_templates
    op.create_table(
        'email_templates',
        sa.Column('template_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), unique=True, nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('template_id')
    )

    # 19. email_queue
    op.create_table(
        'email_queue',
        sa.Column('email_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=False),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('email_id')
    )

    # 20. cache_metadata
    op.create_table(
        'cache_metadata',
        sa.Column('cache_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=255), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('cache_id')
    )


def downgrade() -> None:
    op.drop_table('cache_metadata')
    op.drop_table('email_queue')
    op.drop_table('email_templates')
    op.drop_table('system_settings')
    op.drop_table('system_metrics')
    op.drop_table('system_health')
    op.drop_table('job_history')
    op.drop_table('jobs')
    op.drop_table('attachment_versions')
    op.drop_table('attachments')
    op.drop_table('search_index')
    op.drop_table('saved_filters')
    op.drop_table('dashboard_widgets')
    op.drop_table('scheduled_reports')
    op.drop_table('reports')
    op.drop_table('activity_logs')
    op.drop_table('audit_logs')
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
    op.drop_table('notification_templates')
