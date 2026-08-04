"""add_procurement_and_vendor_lifecycle_tables

Revision ID: c5d1670b586c
Revises: 20260803_pr_lifecycle
Create Date: 2026-08-03 15:53:55.895601

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5d1670b586c'
down_revision: Union[str, Sequence[str], None] = '20260803_pr_lifecycle'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. vendors
    op.create_table(
        'vendors',
        sa.Column('vendor_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('vendor_code', sa.String(length=50), unique=True, nullable=False),
        sa.Column('vendor_name', sa.String(length=255), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=True),
        sa.Column('gst_vat_number', sa.String(length=50), nullable=True),
        sa.Column('tax_number', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=True),
        sa.Column('preferred_vendor', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Active', nullable=True),
        sa.Column('blacklist_status', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('payment_terms', sa.String(length=255), nullable=True),
        sa.Column('delivery_terms', sa.String(length=255), nullable=True),
        sa.Column('bank_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('vendor_id')
    )

    # 2. vendor_contacts
    op.create_table(
        'vendor_contacts',
        sa.Column('contact_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('contact_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('contact_id')
    )

    # 3. vendor_documents
    op.create_table(
        'vendor_documents',
        sa.Column('document_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('document_type', sa.String(length=100), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id')
    )

    # 4. vendor_categories
    op.create_table(
        'vendor_categories',
        sa.Column('category_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('category_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('category_id')
    )

    # 5. vendor_performance
    op.create_table(
        'vendor_performance',
        sa.Column('performance_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('delivery_performance', sa.Numeric(5, 2), server_default='100.00', nullable=True),
        sa.Column('quality_score', sa.Numeric(5, 2), server_default='100.00', nullable=True),
        sa.Column('response_time', sa.Numeric(5, 2), server_default='100.00', nullable=True),
        sa.Column('contract_compliance', sa.Numeric(5, 2), server_default='100.00', nullable=True),
        sa.Column('purchase_volume', sa.Numeric(15, 2), server_default='0.00', nullable=True),
        sa.Column('avg_lead_time_days', sa.Numeric(5, 2), server_default='0.00', nullable=True),
        sa.Column('rating', sa.Numeric(3, 2), server_default='5.00', nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('performance_id')
    )

    # 6. vendor_blacklist
    op.create_table(
        'vendor_blacklist',
        sa.Column('blacklist_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('blacklisted_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['blacklisted_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('blacklist_id')
    )

    # 7. request_for_quotations
    op.create_table(
        'request_for_quotations',
        sa.Column('rfq_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('rfq_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('pr_id', sa.BigInteger(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Draft', nullable=True),
        sa.Column('submission_deadline', sa.DateTime(), nullable=True),
        sa.Column('closing_date', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['pr_id'], ['purchase_requisitions.pr_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('rfq_id')
    )

    # 8. rfq_items
    op.create_table(
        'rfq_items',
        sa.Column('rfq_item_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('rfq_id', sa.BigInteger(), nullable=True),
        sa.Column('pr_item_id', sa.BigInteger(), nullable=True),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('specification', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['rfq_id'], ['request_for_quotations.rfq_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pr_item_id'], ['pr_items.pr_item_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('rfq_item_id')
    )

    # 9. rfq_vendors
    op.create_table(
        'rfq_vendors',
        sa.Column('rfq_vendor_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('rfq_id', sa.BigInteger(), nullable=True),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('invited_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['rfq_id'], ['request_for_quotations.rfq_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('rfq_vendor_id')
    )

    # 10. vendor_quotations
    op.create_table(
        'vendor_quotations',
        sa.Column('quotation_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('quotation_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('rfq_id', sa.BigInteger(), nullable=True),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('total_amount', sa.Numeric(15, 2), server_default='0.00', nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('warranty_months', sa.Integer(), nullable=True),
        sa.Column('technical_proposal', sa.Text(), nullable=True),
        sa.Column('commercial_proposal', sa.Text(), nullable=True),
        sa.Column('technical_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('commercial_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Submitted', nullable=True),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['rfq_id'], ['request_for_quotations.rfq_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('quotation_id')
    )

    # 11. quotation_items
    op.create_table(
        'quotation_items',
        sa.Column('quotation_item_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.BigInteger(), nullable=True),
        sa.Column('rfq_item_id', sa.BigInteger(), nullable=True),
        sa.Column('unit_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(15, 2), server_default='0.00', nullable=True),
        sa.Column('discount_amount', sa.Numeric(15, 2), server_default='0.00', nullable=True),
        sa.Column('total_price', sa.Numeric(15, 2), nullable=False),
        sa.ForeignKeyConstraint(['quotation_id'], ['vendor_quotations.quotation_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rfq_item_id'], ['rfq_items.rfq_item_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('quotation_item_id')
    )

    # 12. quotation_comparison
    op.create_table(
        'quotation_comparison',
        sa.Column('comparison_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('rfq_id', sa.BigInteger(), nullable=True),
        sa.Column('winner_technical_quotation_id', sa.BigInteger(), nullable=True),
        sa.Column('winner_commercial_quotation_id', sa.BigInteger(), nullable=True),
        sa.Column('final_selected_vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('final_selected_quotation_id', sa.BigInteger(), nullable=True),
        sa.Column('selection_reason', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.BigInteger(), nullable=True),
        sa.Column('actioned_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['rfq_id'], ['request_for_quotations.rfq_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['winner_technical_quotation_id'], ['vendor_quotations.quotation_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['winner_commercial_quotation_id'], ['vendor_quotations.quotation_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['final_selected_vendor_id'], ['vendors.vendor_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['final_selected_quotation_id'], ['vendor_quotations.quotation_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('comparison_id')
    )

    # 13. purchase_orders
    op.create_table(
        'purchase_orders',
        sa.Column('po_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('po_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('rfq_id', sa.BigInteger(), nullable=True),
        sa.Column('pr_id', sa.BigInteger(), nullable=True),
        sa.Column('department_id', sa.BigInteger(), nullable=True),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(15, 2), server_default='0.00', nullable=True),
        sa.Column('discount_amount', sa.Numeric(15, 2), server_default='0.00', nullable=True),
        sa.Column('grand_total', sa.Numeric(15, 2), nullable=False),
        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('billing_address', sa.Text(), nullable=True),
        sa.Column('payment_terms', sa.String(length=255), nullable=True),
        sa.Column('delivery_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Draft', nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['rfq_id'], ['request_for_quotations.rfq_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pr_id'], ['purchase_requisitions.pr_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.department_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('po_id')
    )

    # 14. purchase_order_items
    op.create_table(
        'purchase_order_items',
        sa.Column('po_item_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('po_id', sa.BigInteger(), nullable=True),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('specification', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(15, 2), nullable=False),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('po_item_id')
    )

    # 15. po_approval
    op.create_table(
        'po_approval',
        sa.Column('approval_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('po_id', sa.BigInteger(), nullable=True),
        sa.Column('approver_id', sa.BigInteger(), nullable=True),
        sa.Column('role_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('actioned_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.user_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('approval_id')
    )

    # 16. contracts
    op.create_table(
        'contracts',
        sa.Column('contract_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('contract_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('contract_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Draft', nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('renewal_date', sa.Date(), nullable=True),
        sa.Column('expiry_reminder_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('contract_id')
    )

    # 17. contract_documents
    op.create_table(
        'contract_documents',
        sa.Column('document_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('contract_id', sa.BigInteger(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.contract_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id')
    )

    # 18. subscription_contracts
    op.create_table(
        'subscription_contracts',
        sa.Column('subscription_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('contract_id', sa.BigInteger(), nullable=True),
        sa.Column('license_count', sa.Integer(), nullable=False),
        sa.Column('billing_frequency', sa.String(length=50), nullable=False),
        sa.Column('unit_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), server_default='false', nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.contract_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('subscription_id')
    )

    # 19. amc_contracts
    op.create_table(
        'amc_contracts',
        sa.Column('amc_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('contract_id', sa.BigInteger(), nullable=True),
        sa.Column('coverage_details', sa.Text(), nullable=True),
        sa.Column('response_sla_hours', sa.Integer(), nullable=True),
        sa.Column('scheduled_visits_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.contract_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('amc_id')
    )

    # 20. rate_contracts
    op.create_table(
        'rate_contracts',
        sa.Column('rate_contract_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('contract_id', sa.BigInteger(), nullable=True),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('specification', sa.Text(), nullable=True),
        sa.Column('pre_negotiated_unit_price', sa.Numeric(15, 2), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.contract_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('rate_contract_id')
    )


def downgrade() -> None:
    op.drop_table('rate_contracts')
    op.drop_table('amc_contracts')
    op.drop_table('subscription_contracts')
    op.drop_table('contract_documents')
    op.drop_table('contracts')
    op.drop_table('po_approval')
    op.drop_table('purchase_order_items')
    op.drop_table('purchase_orders')
    op.drop_table('quotation_comparison')
    op.drop_table('quotation_items')
    op.drop_table('vendor_quotations')
    op.drop_table('rfq_vendors')
    op.drop_table('rfq_items')
    op.drop_table('request_for_quotations')
    op.drop_table('vendor_blacklist')
    op.drop_table('vendor_performance')
    op.drop_table('vendor_categories')
    op.drop_table('vendor_documents')
    op.drop_table('vendor_contacts')
    op.drop_table('vendors')
