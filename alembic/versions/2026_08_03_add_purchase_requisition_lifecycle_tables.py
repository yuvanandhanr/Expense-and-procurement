"""add_purchase_requisition_lifecycle_tables

Revision ID: 20260803_pr_lifecycle
Revises: 20260803_identity_org
Create Date: 2026-08-03 16:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260803_pr_lifecycle'
down_revision = '20260803_identity_org'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add fields to purchase_requisitions table
    op.add_column('purchase_requisitions', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('purchase_requisitions', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('purchase_requisitions', sa.Column('priority', sa.String(length=50), server_default='Medium', nullable=True))
    op.add_column('purchase_requisitions', sa.Column('purchase_type', sa.String(length=50), server_default='Standard', nullable=True))
    op.add_column('purchase_requisitions', sa.Column('currency', sa.String(length=10), server_default='USD', nullable=True))
    op.add_column('purchase_requisitions', sa.Column('need_by_date', sa.DateTime(), nullable=True))
    op.add_column('purchase_requisitions', sa.Column('project_code', sa.String(length=50), nullable=True))

    # Create approval_matrix table
    op.create_table(
        'approval_matrix',
        sa.Column('matrix_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('department_id', sa.BigInteger(), nullable=True),
        sa.Column('cost_center_id', sa.BigInteger(), nullable=True),
        sa.Column('purchase_type', sa.String(length=50), nullable=True),
        sa.Column('min_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('max_amount', sa.Numeric(precision=15, scale=2), server_default='99999999.99', nullable=True),
        sa.Column('approval_level', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.department_id'], name='approval_matrix_department_id_fkey', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cost_center_id'], ['cost_centres.cost_center_id'], name='approval_matrix_cost_center_id_fkey', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], name='approval_matrix_role_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('matrix_id')
    )

    # Create approval_workflows table
    op.create_table(
        'approval_workflows',
        sa.Column('workflow_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pr_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Under Review', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['pr_id'], ['purchase_requisitions.pr_id'], name='approval_workflows_pr_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('workflow_id')
    )

    # Create approval_steps table
    op.create_table(
        'approval_steps',
        sa.Column('step_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('workflow_id', sa.BigInteger(), nullable=True),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('approver_role_id', sa.BigInteger(), nullable=True),
        sa.Column('approver_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=True),
        sa.Column('actioned_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['approval_workflows.workflow_id'], name='approval_steps_workflow_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_role_id'], ['roles.role_id'], name='approval_steps_approver_role_id_fkey', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.user_id'], name='approval_steps_approver_id_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('step_id')
    )

    # Create workflow_history table
    op.create_table(
        'workflow_history',
        sa.Column('history_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pr_id', sa.BigInteger(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('performed_by', sa.BigInteger(), nullable=True),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['pr_id'], ['purchase_requisitions.pr_id'], name='workflow_history_pr_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.user_id'], name='workflow_history_performed_by_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('history_id')
    )

    # Create approval_history table
    op.create_table(
        'approval_history',
        sa.Column('history_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('step_id', sa.BigInteger(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('performed_by', sa.BigInteger(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['step_id'], ['approval_steps.step_id'], name='approval_history_step_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.user_id'], name='approval_history_performed_by_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('history_id')
    )

    # Create approval_comments table
    op.create_table(
        'approval_comments',
        sa.Column('comment_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pr_id', sa.BigInteger(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', sa.BigInteger(), nullable=True),
        sa.Column('is_internal', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['pr_id'], ['purchase_requisitions.pr_id'], name='approval_comments_pr_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name='approval_comments_user_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['approval_comments.comment_id'], name='approval_comments_parent_comment_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('comment_id')
    )

    # Create budget_allocations table
    op.create_table(
        'budget_allocations',
        sa.Column('allocation_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('budget_code_id', sa.BigInteger(), nullable=False),
        sa.Column('allocated_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('spent_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('reserved_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('fiscal_year', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='Active', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['budget_code_id'], ['budget_codes.budget_code_id'], name='budget_allocations_budget_code_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('allocation_id')
    )

    # Create budget_reservations table
    op.create_table(
        'budget_reservations',
        sa.Column('reservation_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pr_id', sa.BigInteger(), nullable=False),
        sa.Column('budget_code_id', sa.BigInteger(), nullable=False),
        sa.Column('reserved_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Reserved', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('released_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pr_id'], ['purchase_requisitions.pr_id'], name='budget_reservations_pr_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['budget_code_id'], ['budget_codes.budget_code_id'], name='budget_reservations_budget_code_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('reservation_id')
    )

    # Create pr_attachments table
    op.create_table(
        'pr_attachments',
        sa.Column('attachment_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pr_id', sa.BigInteger(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['pr_id'], ['purchase_requisitions.pr_id'], name='pr_attachments_pr_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.user_id'], name='pr_attachments_uploaded_by_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('attachment_id')
    )


def downgrade() -> None:
    op.drop_table('pr_attachments')
    op.drop_table('budget_reservations')
    op.drop_table('budget_allocations')
    op.drop_table('approval_comments')
    op.drop_table('approval_history')
    op.drop_table('workflow_history')
    op.drop_table('approval_steps')
    op.drop_table('approval_workflows')
    op.drop_table('approval_matrix')
    op.drop_column('purchase_requisitions', 'project_code')
    op.drop_column('purchase_requisitions', 'need_by_date')
    op.drop_column('purchase_requisitions', 'currency')
    op.drop_column('purchase_requisitions', 'purchase_type')
    op.drop_column('purchase_requisitions', 'priority')
    op.drop_column('purchase_requisitions', 'description')
    op.drop_column('purchase_requisitions', 'title')
