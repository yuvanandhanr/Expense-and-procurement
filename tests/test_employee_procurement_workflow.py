import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, date
from decimal import Decimal

from src.models.auth import User, Role
from src.models.purchase_requisition import PurchaseRequisition
from src.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from src.models.grn import GoodsReceipt
from src.models.inspection import InspectionReport, InspectionItem
from src.schemas.grn import GRNCreate, GRNItemCreate

@pytest.fixture
def mock_employee() -> User:
    role = Role(role_id=1, role_name="Employee", status=True)
    return User(
        user_id=1,
        employee_code="EMP001",
        email="emp@example.com",
        status="Active",
        roles=[role]
    )

@pytest.fixture
def mock_proc_officer() -> User:
    role = Role(role_id=2, role_name="Procurement Officer", status=True)
    return User(
        user_id=2,
        employee_code="PROC001",
        email="proc@example.com",
        status="Active",
        roles=[role]
    )

@pytest.fixture
def authenticate_officer(mock_proc_officer):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_proc_officer
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.anyio
@patch("src.services.grn_service.PORepository", autospec=True)
@patch("src.services.grn_service.PRRepository", autospec=True)
@patch("src.services.grn_service.InspectionRepository", autospec=True)
@patch("src.services.grn_service.AssetService", autospec=True)
@patch("src.services.grn_service.GRNRepository", autospec=True)
@patch("src.services.grn_service.GRNItemRepository", autospec=True)
async def test_grn_auto_asset_assignment_to_requestor(
    mock_grn_item_repo_cls,
    mock_grn_repo_cls,
    mock_asset_service_cls,
    mock_inspection_repo_cls,
    mock_pr_repo_cls,
    mock_po_repo_cls,
    authenticate_officer,
    async_client: AsyncClient
):
    # Setup Mocks
    mock_po_repo = mock_po_repo_cls.return_value
    mock_pr_repo = mock_pr_repo_cls.return_value
    mock_inspection_repo = mock_inspection_repo_cls.return_value
    mock_asset_service = mock_asset_service_cls.return_value
    mock_grn_repo = mock_grn_repo_cls.return_value
    mock_grn_item_repo = mock_grn_item_repo_cls.return_value

    # PO mock
    po_item = PurchaseOrderItem(
        po_item_id=1,
        po_id=1,
        item_name="MacBook Pro",
        quantity=1,
        unit_price=Decimal("2000.00"),
        total_price=Decimal("2000.00")
    )
    po = PurchaseOrder(
        po_id=1,
        pr_id=99,
        vendor_id=5,
        total_amount=Decimal("2000.00"),
        grand_total=Decimal("2000.00"),
        status="Approved",
        items=[po_item]
    )
    mock_po_repo.get_by_id.return_value = po
    mock_po_repo.update = AsyncMock()

    # PR mock (has requestor)
    pr = PurchaseRequisition(
        pr_id=99,
        requestor_id=10 # The employee who requested it
    )
    mock_pr_repo.get_by_id.return_value = pr

    # Inspection mock
    inspection_item = InspectionItem(
        inspection_item_id=1,
        inspection_id=1,
        delivery_item_id=1,
        quantity_inspected=1,
        quantity_accepted=1,
        quantity_rejected=0,
        serial_numbers="SN12345"
    )
    # mock delivery_item relationship
    mock_del_item = MagicMock()
    mock_del_item.item_name = "MacBook Pro"
    inspection_item.delivery_item = mock_del_item
    
    inspection = InspectionReport(
        inspection_id=1,
        delivery_id=1,
        inspected_by=2,
        outcome="Accepted",
        items=[inspection_item]
    )
    mock_inspection_repo.get_by_id.return_value = inspection

    # GRN Repo mock
    grn = GoodsReceipt(
        grn_id=1,
        grn_number="GRN-TEST-123",
        po_id=1,
        status="Completed",
        created_at=datetime.utcnow(),
        items=[]
    )
    mock_grn_repo.create.return_value = grn
    mock_grn_repo.get_by_id.return_value = grn
    
    mock_grn_item_repo.create = AsyncMock()

    # Asset Service Mock
    mock_asset_service.register_assets_from_grn = AsyncMock()

    response = await async_client.post(
        "/api/v1/grn",
        json={
            "po_id": 1,
            "vendor_id": 5,
            "delivery_id": 1,
            "inspection_id": 1,
            "warehouse": "Main IT Room",
            "notes": "All good",
            "items": []
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "Completed"

    # Verify asset service was called with requestor_id=10
    mock_asset_service.register_assets_from_grn.assert_called_once_with(
        po_id=1,
        vendor_id=5,
        item_name="MacBook Pro",
        quantity=1,
        serial_numbers="SN12345",
        requestor_id=10
    )


@pytest.mark.anyio
@patch("src.services.grn_service.PORepository", autospec=True)
@patch("src.services.grn_service.PRRepository", autospec=True)
@patch("src.services.grn_service.InspectionRepository", autospec=True)
@patch("src.services.grn_service.AssetService", autospec=True)
@patch("src.services.grn_service.GRNRepository", autospec=True)
@patch("src.services.grn_service.GRNItemRepository", autospec=True)
async def test_grn_physical_inspection_fail(
    mock_grn_item_repo_cls,
    mock_grn_repo_cls,
    mock_asset_service_cls,
    mock_inspection_repo_cls,
    mock_pr_repo_cls,
    mock_po_repo_cls,
    authenticate_officer,
    async_client: AsyncClient
):
    mock_po_repo = mock_po_repo_cls.return_value
    mock_pr_repo = mock_pr_repo_cls.return_value
    mock_inspection_repo = mock_inspection_repo_cls.return_value
    mock_asset_service = mock_asset_service_cls.return_value
    mock_grn_repo = mock_grn_repo_cls.return_value
    mock_grn_item_repo = mock_grn_item_repo_cls.return_value

    po_item = PurchaseOrderItem(po_item_id=1, po_id=1, item_name="MacBook Pro", quantity=1)
    po = PurchaseOrder(po_id=1, pr_id=99, vendor_id=5, status="Approved", items=[po_item])
    mock_po_repo.get_by_id.return_value = po
    mock_po_repo.update = AsyncMock()

    pr = PurchaseRequisition(pr_id=99, requestor_id=10)
    mock_pr_repo.get_by_id.return_value = pr

    inspection_item = InspectionItem(
        inspection_item_id=1, inspection_id=1, delivery_item_id=1,
        quantity_inspected=1, quantity_accepted=0, quantity_rejected=1, serial_numbers=""
    )
    mock_del_item = MagicMock()
    mock_del_item.item_name = "MacBook Pro"
    inspection_item.delivery_item = mock_del_item
    
    inspection = InspectionReport(
        inspection_id=1, delivery_id=1, outcome="Rejected", items=[inspection_item]
    )
    mock_inspection_repo.get_by_id.return_value = inspection

    grn = GoodsReceipt(
        grn_id=1, grn_number="GRN-TEST-123", po_id=1, status="Rejected", created_at=datetime.utcnow(), items=[]
    )
    mock_grn_repo.create.return_value = grn
    mock_grn_repo.get_by_id.return_value = grn
    mock_grn_item_repo.create = AsyncMock()
    mock_asset_service.register_assets_from_grn = AsyncMock()

    response = await async_client.post(
        "/api/v1/grn",
        json={"po_id": 1, "vendor_id": 5, "delivery_id": 1, "inspection_id": 1, "items": []}
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["status"] == "Rejected"
    mock_asset_service.register_assets_from_grn.assert_not_called()
    assert po.status == "Delivery Rejected"

@pytest.fixture
def mock_manager() -> User:
    role = Role(role_id=2, role_name="Manager", status=True)
    return User(
        user_id=2,
        employee_code="MGR001",
        email="manager@example.com",
        status="Active",
        roles=[role]
    )

@pytest.fixture
def mock_finance_manager() -> User:
    role = Role(role_id=3, role_name="Finance Manager", status=True)
    return User(
        user_id=3,
        employee_code="FIN001",
        email="finance@example.com",
        status="Active",
        roles=[role]
    )

@pytest.mark.anyio
@patch("src.api.approvals.get_current_user")
@patch("src.api.approvals.verify_approver_role", new_callable=AsyncMock)
@patch("src.services.approval_service.PRRepository", autospec=True)
@patch("src.services.approval_service.ApprovalWorkflowRepository", autospec=True)
@patch("src.services.approval_service.ApprovalStepRepository", autospec=True)
@patch("src.services.approval_service.ApprovalHistoryRepository", autospec=True)
@patch("src.services.approval_service.WorkflowHistoryRepository", autospec=True)
@patch("src.services.budget_service.BudgetService", autospec=True)
@patch("src.services.rfq_service.RFQService")
async def test_dept_manager_approve(
    mock_rfq_service,
    mock_budget_service,
    mock_workflow_hist_repo_cls,
    mock_approval_hist_repo_cls,
    mock_step_repo_cls,
    mock_wf_repo_cls,
    mock_pr_repo_cls,
    mock_verify_role,
    mock_current_user,
    mock_manager,
    async_client: AsyncClient,
    override_db
):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_manager
    mock_current_user.return_value = mock_manager

    mock_pr_repo = mock_pr_repo_cls.return_value
    mock_wf_repo = mock_wf_repo_cls.return_value
    mock_step_repo = mock_step_repo_cls.return_value

    pr = PurchaseRequisition(
        pr_id=1, 
        requestor_id=10, 
        status="Pending Manager Approval", 
        title="Test",
        justification="Test",
        pr_number="PR-001",
        total_estimated_amount=Decimal("100.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_pr_repo.get_by_id.return_value = pr
    mock_pr_repo.update = AsyncMock()

    wf = MagicMock()
    wf.workflow_id = 1
    mock_wf_repo.get_by_pr_id.return_value = wf

    # Mock steps
    active_step = MagicMock()
    active_step.step_id = 1
    active_step.workflow_id = 1
    active_step.step_number = 1
    active_step.approver_role_id = 2
    active_step.status = "Pending"

    next_step = MagicMock()
    next_step.step_id = 2
    next_step.approver_role_id = 3
    next_step.step_number = 2

    mock_step_repo.get_active_step_for_workflow.side_effect = [active_step, next_step, next_step]
    mock_step_repo.update = AsyncMock()

    # Mock db.execute to return nothing for duplicate check
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    override_db.execute = AsyncMock(return_value=mock_result)

    with patch("src.services.approval_service.ApprovalService._get_status_from_role_id", AsyncMock(return_value="Pending Finance Manager Approval")):
        response = await async_client.post("/api/v1/pr/1/approve", json={"comments": "Approved by manager"})

    assert response.status_code == 200
    assert response.json()["status"] == "Pending Finance Manager Approval"
    active_step.status == "Approved"
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.anyio
@patch("src.api.approvals.get_current_user")
@patch("src.api.approvals.verify_approver_role", new_callable=AsyncMock)
@patch("src.services.approval_service.PRRepository", autospec=True)
@patch("src.services.approval_service.ApprovalWorkflowRepository", autospec=True)
@patch("src.services.approval_service.ApprovalStepRepository", autospec=True)
@patch("src.services.approval_service.ApprovalHistoryRepository", autospec=True)
@patch("src.services.approval_service.WorkflowHistoryRepository", autospec=True)
@patch("src.services.budget_service.BudgetService", autospec=True)
@patch("src.services.notification_service.NotificationService", autospec=True)
async def test_dept_manager_reject(
    mock_notification_service_cls,
    mock_budget_service,
    mock_workflow_hist_repo_cls,
    mock_approval_hist_repo_cls,
    mock_step_repo_cls,
    mock_wf_repo_cls,
    mock_pr_repo_cls,
    mock_verify_role,
    mock_current_user,
    mock_manager,
    async_client: AsyncClient,
):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_manager
    mock_current_user.return_value = mock_manager

    mock_pr_repo = mock_pr_repo_cls.return_value
    mock_wf_repo = mock_wf_repo_cls.return_value
    mock_step_repo = mock_step_repo_cls.return_value

    pr = PurchaseRequisition(
        pr_id=1, 
        requestor_id=10, 
        status="Pending Manager Approval",
        title="Test",
        justification="Test",
        pr_number="PR-001",
        total_estimated_amount=Decimal("100.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_pr_repo.get_by_id.return_value = pr
    mock_pr_repo.update = AsyncMock()

    wf = MagicMock()
    wf.workflow_id = 1
    mock_wf_repo.get_by_pr_id.return_value = wf

    active_step = MagicMock()
    active_step.step_id = 1
    active_step.workflow_id = 1
    active_step.status = "Pending"
    mock_step_repo.get_active_step_for_workflow.return_value = active_step

    response = await async_client.post("/api/v1/pr/1/reject", json={"comments": "Rejected by manager"})

    assert response.status_code == 200
    assert response.json()["status"] == "Rejected"
    assert wf.status == "Rejected"
    assert active_step.status == "Rejected"
    
    mock_notification_service_cls.return_value.send_notification.assert_called_once()
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.anyio
@patch("src.api.approvals.get_current_user")
@patch("src.api.approvals.verify_approver_role", new_callable=AsyncMock)
@patch("src.services.approval_service.PRRepository", autospec=True)
@patch("src.services.approval_service.ApprovalWorkflowRepository", autospec=True)
@patch("src.services.approval_service.ApprovalStepRepository", autospec=True)
@patch("src.services.approval_service.ApprovalHistoryRepository", autospec=True)
@patch("src.services.approval_service.WorkflowHistoryRepository", autospec=True)
@patch("src.services.budget_service.BudgetService", autospec=True)
@patch("src.services.notification_service.NotificationService", autospec=True)
async def test_finance_manager_reject(
    mock_notification_service_cls,
    mock_budget_service,
    mock_workflow_hist_repo_cls,
    mock_approval_hist_repo_cls,
    mock_step_repo_cls,
    mock_wf_repo_cls,
    mock_pr_repo_cls,
    mock_verify_role,
    mock_current_user,
    mock_finance_manager,
    async_client: AsyncClient,
):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_finance_manager
    mock_current_user.return_value = mock_finance_manager

    mock_pr_repo = mock_pr_repo_cls.return_value
    mock_wf_repo = mock_wf_repo_cls.return_value
    mock_step_repo = mock_step_repo_cls.return_value

    pr = PurchaseRequisition(
        pr_id=1, 
        requestor_id=10, 
        status="Pending Finance Manager Approval",
        title="Test",
        justification="Test",
        pr_number="PR-001",
        total_estimated_amount=Decimal("100.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_pr_repo.get_by_id.return_value = pr
    mock_pr_repo.update = AsyncMock()

    wf = MagicMock()
    wf.workflow_id = 1
    mock_wf_repo.get_by_pr_id.return_value = wf

    active_step = MagicMock()
    active_step.step_id = 2
    active_step.workflow_id = 1
    active_step.status = "Pending"
    mock_step_repo.get_active_step_for_workflow.return_value = active_step

    response = await async_client.post("/api/v1/pr/1/reject", json={"comments": "Rejected by finance manager"})

    assert response.status_code == 200
    assert response.json()["status"] == "Rejected"
    
    mock_notification_service_cls.return_value.send_notification.assert_called_once()
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.anyio
@patch("src.api.invoices.get_current_user")
@patch("src.api.invoices.select")
async def test_3way_invoice_mismatch(
    mock_select,
    mock_current_user,
    mock_finance_manager,
    async_client: AsyncClient,
    override_db
):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_finance_manager
    mock_current_user.return_value = mock_finance_manager

    # Mock DB response for invoice
    mock_po = MagicMock()
    mock_po.grand_total = Decimal("6000.00")

    mock_invoice = MagicMock()
    mock_invoice.invoice_id = 1
    mock_invoice.po_id = 1
    mock_invoice.grand_total = Decimal("5000.00")
    mock_invoice.po = mock_po

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_invoice
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.post("/api/v1/invoices/1/approve")
    
    assert response.status_code == 400
    assert "3-way match failed" in response.json()["detail"]
    app.dependency_overrides.pop(get_current_user, None)

