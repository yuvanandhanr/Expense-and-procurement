"""add_p2p_and_asset_management_tables

Revision ID: 0970733350dd
Revises: c5d1670b586c
Create Date: 2026-08-03 16:23:42.475846

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0970733350dd'
down_revision: Union[str, Sequence[str], None] = 'c5d1670b586c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. deliveries
    op.create_table(
        'deliveries',
        sa.Column('delivery_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('po_id', sa.BigInteger(), nullable=True),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('delivery_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('delivery_date', sa.DateTime(), nullable=True),
        sa.Column('expected_date', sa.DateTime(), nullable=True),
        sa.Column('delivered_by', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=True),
        sa.Column('delivery_notes', sa.Text(), nullable=True),
        sa.Column('carrier', sa.String(length=100), nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('delivery_id')
    )

    # 2. delivery_items
    op.create_table(
        'delivery_items',
        sa.Column('delivery_item_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('delivery_id', sa.BigInteger(), nullable=True),
        sa.Column('po_item_id', sa.BigInteger(), nullable=True),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('quantity_shipped', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['delivery_id'], ['deliveries.delivery_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['po_item_id'], ['purchase_order_items.po_item_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('delivery_item_id')
    )

    # 3. inspection_reports
    op.create_table(
        'inspection_reports',
        sa.Column('inspection_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('delivery_id', sa.BigInteger(), nullable=True),
        sa.Column('inspected_by', sa.BigInteger(), nullable=True),
        sa.Column('inspection_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('damage_check_passed', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('specification_check_passed', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('quantity_verified', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['delivery_id'], ['deliveries.delivery_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspected_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('inspection_id')
    )

    # 4. inspection_items
    op.create_table(
        'inspection_items',
        sa.Column('inspection_item_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('inspection_id', sa.BigInteger(), nullable=True),
        sa.Column('delivery_item_id', sa.BigInteger(), nullable=True),
        sa.Column('quantity_inspected', sa.Integer(), nullable=False),
        sa.Column('quantity_accepted', sa.Integer(), nullable=False),
        sa.Column('quantity_rejected', sa.Integer(), nullable=False),
        sa.Column('serial_numbers', sa.Text(), nullable=True),
        sa.Column('license_keys', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspection_reports.inspection_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['delivery_item_id'], ['delivery_items.delivery_item_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('inspection_item_id')
    )

    # 5. goods_receipts
    op.create_table(
        'goods_receipts',
        sa.Column('grn_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('grn_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('po_id', sa.BigInteger(), nullable=True),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('delivery_id', sa.BigInteger(), nullable=True),
        sa.Column('inspection_id', sa.BigInteger(), nullable=True),
        sa.Column('warehouse', sa.String(length=100), nullable=True),
        sa.Column('received_by', sa.BigInteger(), nullable=True),
        sa.Column('received_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['delivery_id'], ['deliveries.delivery_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspection_reports.inspection_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['received_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('grn_id')
    )

    # 6. goods_receipt_items
    op.create_table(
        'goods_receipt_items',
        sa.Column('grn_item_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('grn_id', sa.BigInteger(), nullable=True),
        sa.Column('delivery_item_id', sa.BigInteger(), nullable=True),
        sa.Column('quantity_received', sa.Integer(), nullable=False),
        sa.Column('quantity_rejected', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['grn_id'], ['goods_receipts.grn_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['delivery_item_id'], ['delivery_items.delivery_item_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('grn_item_id')
    )

    # 7. asset_categories
    op.create_table(
        'asset_categories',
        sa.Column('category_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('category_name', sa.String(length=100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('category_id')
    )

    # 8. assets
    op.create_table(
        'assets',
        sa.Column('asset_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('asset_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('asset_tag', sa.String(length=100), unique=True, nullable=False),
        sa.Column('category_id', sa.BigInteger(), nullable=True),
        sa.Column('po_id', sa.BigInteger(), nullable=True),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('department_id', sa.BigInteger(), nullable=True),
        sa.Column('assigned_employee_id', sa.BigInteger(), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('warranty_expiry', sa.Date(), nullable=True),
        sa.Column('amc_expiry', sa.Date(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Available', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['asset_categories.category_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.department_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_employee_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('asset_id')
    )

    # 9. asset_assignments
    op.create_table(
        'asset_assignments',
        sa.Column('assignment_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.BigInteger(), nullable=True),
        sa.Column('assigned_to', sa.BigInteger(), nullable=True),
        sa.Column('assigned_by', sa.BigInteger(), nullable=True),
        sa.Column('assigned_date', sa.Date(), nullable=False),
        sa.Column('return_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('assignment_id')
    )

    # 10. asset_history
    op.create_table(
        'asset_history',
        sa.Column('history_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.BigInteger(), nullable=True),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_by', sa.BigInteger(), nullable=True),
        sa.Column('action_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['action_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('history_id')
    )

    # 11. asset_documents
    op.create_table(
        'asset_documents',
        sa.Column('document_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.BigInteger(), nullable=True),
        sa.Column('document_type', sa.String(length=100), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id')
    )

    # 12. vendor_invoices
    op.create_table(
        'vendor_invoices',
        sa.Column('invoice_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=True),
        sa.Column('po_id', sa.BigInteger(), nullable=True),
        sa.Column('grn_id', sa.BigInteger(), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('taxes', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('discount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('grand_total', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Draft', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.vendor_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['grn_id'], ['goods_receipts.grn_id'], ondelete='SET NULL'),
        sa.UniqueConstraint('vendor_id', 'invoice_number', name='unique_vendor_invoice'),
        sa.PrimaryKeyConstraint('invoice_id')
    )

    # 13. invoice_items
    op.create_table(
        'invoice_items',
        sa.Column('invoice_item_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.BigInteger(), nullable=True),
        sa.Column('po_item_id', sa.BigInteger(), nullable=True),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['vendor_invoices.invoice_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['po_item_id'], ['purchase_order_items.po_item_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('invoice_item_id')
    )

    # 14. invoice_documents
    op.create_table(
        'invoice_documents',
        sa.Column('document_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.BigInteger(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['vendor_invoices.invoice_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id')
    )

    # 15. invoice_approval
    op.create_table(
        'invoice_approval',
        sa.Column('approval_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.BigInteger(), nullable=True),
        sa.Column('approver_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('actioned_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['vendor_invoices.invoice_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('approval_id')
    )

    # 16. three_way_matching
    op.create_table(
        'three_way_matching',
        sa.Column('matching_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.BigInteger(), nullable=True),
        sa.Column('po_id', sa.BigInteger(), nullable=True),
        sa.Column('grn_id', sa.BigInteger(), nullable=True),
        sa.Column('item_match_passed', sa.Boolean(), nullable=False),
        sa.Column('quantity_match_passed', sa.Boolean(), nullable=False),
        sa.Column('price_match_passed', sa.Boolean(), nullable=False),
        sa.Column('tax_match_passed', sa.Boolean(), nullable=False),
        sa.Column('currency_match_passed', sa.Boolean(), nullable=False),
        sa.Column('total_amount_match_passed', sa.Boolean(), nullable=False),
        sa.Column('variance_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('match_result', sa.String(length=50), nullable=False),
        sa.Column('inspected_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['vendor_invoices.invoice_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['grn_id'], ['goods_receipts.grn_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('matching_id')
    )

    # 17. payment_requests
    op.create_table(
        'payment_requests',
        sa.Column('payment_request_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.BigInteger(), nullable=True),
        sa.Column('po_id', sa.BigInteger(), nullable=True),
        sa.Column('request_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=True),
        sa.Column('payment_readiness_passed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['vendor_invoices.invoice_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('payment_request_id')
    )

    # 18. payment_approvals
    op.create_table(
        'payment_approvals',
        sa.Column('approval_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('payment_request_id', sa.BigInteger(), nullable=True),
        sa.Column('approver_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('actioned_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['payment_request_id'], ['payment_requests.payment_request_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('approval_id')
    )

    # 19. procurement_closure
    op.create_table(
        'procurement_closure',
        sa.Column('closure_id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('po_id', sa.BigInteger(), unique=True, nullable=False),
        sa.Column('closed_by', sa.BigInteger(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('po_completed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('grn_completed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('invoice_approved', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('payment_approved', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('assets_registered', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('audit_comments', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.po_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['closed_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('closure_id')
    )


def downgrade() -> None:
    op.drop_table('procurement_closure')
    op.drop_table('payment_approvals')
    op.drop_table('payment_requests')
    op.drop_table('three_way_matching')
    op.drop_table('invoice_approval')
    op.drop_table('invoice_documents')
    op.drop_table('invoice_items')
    op.drop_table('vendor_invoices')
    op.drop_table('asset_documents')
    op.drop_table('asset_history')
    op.drop_table('asset_assignments')
    op.drop_table('assets')
    op.drop_table('asset_categories')
    op.drop_table('goods_receipt_items')
    op.drop_table('goods_receipts')
    op.drop_table('inspection_items')
    op.drop_table('inspection_reports')
    op.drop_table('delivery_items')
    op.drop_table('deliveries')
