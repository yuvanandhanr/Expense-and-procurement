import jwt
import pytest
from datetime import timezone, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import status
from httpx import AsyncClient
from src.core.config import settings
from src.models.auth import User, Role, Permission, LoginSession
from src.models.organization import Department, CostCenter, BudgetCode
from src.models.purchase_requisition import PurchaseRequisition, PRItem
from src.models.approval import ApprovalWorkflow, ApprovalStep, WorkflowHistory, ApprovalComment
from src.models.budget import BudgetReservation
from src.models.attachment import PRAttachment
from src.repositories.purchase_requisition import PRRepository, PRItemRepository
from src.repositories.approval import ApprovalWorkflowRepository, ApprovalStepRepository, WorkflowHistoryRepository, CommentRepository, ApprovalHistoryRepository
from src.repositories.budget import BudgetReservationRepository, BudgetAllocationRepository
from src.repositories.attachment import PRAttachmentRepository
from src.repositories.organization import BudgetCodeRepository


@pytest.fixture
def mock_employee() -> User:
    role = Role(role_id=1, role_name="Employee", status=True)
    return User(
        user_id=1,
        employee_code="EMP001",
        first_name="Employee",
        last_name="One",
        email="employee@example.com",
        department_id=1,
        status="Active",
        roles=[role]
    )


@pytest.fixture
def mock_manager() -> User:
    role = Role(role_id=2, role_name="Manager", status=True)
    return User(
        user_id=2,
        employee_code="MGR001",
        first_name="Manager",
        last_name="One",
        email="manager@example.com",
        department_id=1,
        status="Active",
        roles=[role]
    )


@pytest.fixture
def mock_finance() -> User:
    role = Role(role_id=3, role_name="Finance", status=True)
    return User(
        user_id=3,
        employee_code="FIN001",
        first_name="Finance",
        last_name="One",
        email="finance@example.com",
        department_id=2,
        status="Active",
        roles=[role]
    )


@pytest.fixture
def mock_admin() -> User:
    role = Role(role_id=4, role_name="Admin", status=True)
    return User(
        user_id=4,
        employee_code="ADM001",
        first_name="Admin",
        last_name="One",
        email="admin@example.com",
        status="Active",
        roles=[role]
    )


@pytest.fixture
def employee_jwt(mock_employee) -> str:
    payload = {"sub": str(mock_employee.user_id), "email": mock_employee.email, "exp": 9999999999}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def manager_jwt(mock_manager) -> str:
    payload = {"sub": str(mock_manager.user_id), "email": mock_manager.email, "exp": 9999999999}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def finance_jwt(mock_finance) -> str:
    payload = {"sub": str(mock_finance.user_id), "email": mock_finance.email, "exp": 9999999999}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def admin_jwt(mock_admin) -> str:
    payload = {"sub": str(mock_admin.user_id), "email": mock_admin.email, "exp": 9999999999}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def authenticate_user(mock_employee):
    """
    Default override setup to act as employee.
    """
    async def _get_current_user_override():
        return mock_employee

    async def _jwt_bearer_override():
        return {"sub": str(mock_employee.user_id), "email": mock_employee.email}

    from src.main import app
    from src.auth.dependencies import get_current_user, JWTBearer

    app.dependency_overrides[get_current_user] = _get_current_user_override
    app.dependency_overrides[JWTBearer] = _jwt_bearer_override
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(JWTBearer, None)


@pytest.fixture
def mock_pr() -> PurchaseRequisition:
    item = PRItem(
        pr_item_id=1,
        pr_id=1,
        category="IT",
        item_name="MacBook Pro",
        specification="M3 Max, 64GB RAM",
        quantity=1,
        unit_price=Decimal("4000.00"),
        total_price=Decimal("4000.00")
    )
    return PurchaseRequisition(
        pr_id=1,
        pr_number="PR-20260803-TEST",
        title="Laptop Upgrade",
        justification="Engineering development needs",
        department_id=1,
        cost_center_id=1,
        budget_code="BC-IT-2026",
        priority="High",
        purchase_type="IT",
        requestor_id=1,
        status="Draft",
        total_estimated_amount=Decimal("4000.00"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        items=[item]
    )


@pytest.fixture
def mock_budget_code() -> BudgetCode:
    return BudgetCode(
        budget_code_id=1,
        budget_code="BC-IT-2026",
        available_budget=Decimal("100000.00"),
        status="Active",
        fiscal_year="FY2026"
    )


# --- 1. PR CRUD TESTS ---

@pytest.mark.anyio
@patch.object(PRRepository, "create", new_callable=AsyncMock)
@patch.object(PRItemRepository, "create", new_callable=AsyncMock)
@patch.object(PRRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(WorkflowHistoryRepository, "create", new_callable=AsyncMock)
async def test_create_pr(
    mock_history,
    mock_get_pr,
    mock_item_create,
    mock_pr_create,
    authenticate_user,
    async_client: AsyncClient,
    override_db,
    mock_pr
):
    mock_pr_create.return_value = mock_pr
    mock_get_pr.return_value = mock_pr

    response = await async_client.post(
        "/api/v1/pr",
        json={
            "title": "Laptop Upgrade",
            "justification": "Engineering development needs",
            "department_id": 1,
            "cost_center_id": 1,
            "budget_code": "BC-IT-2026",
            "priority": "High",
            "purchase_type": "IT",
            "items": [
                {
                    "category": "IT",
                    "item_name": "MacBook Pro",
                    "specification": "M3 Max, 64GB RAM",
                    "quantity": 1,
                    "unit_price": 4000.00
                }
            ]
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["pr_number"] == mock_pr.pr_number
    assert Decimal(response.json()["total_estimated_amount"]) == Decimal("4000.00")


@pytest.mark.anyio
@patch.object(PRRepository, "get_by_id", new_callable=AsyncMock)
async def test_get_pr_details(
    mock_get_pr,
    authenticate_user,
    async_client: AsyncClient,
    override_db,
    mock_pr
):
    mock_get_pr.return_value = mock_pr

    response = await async_client.get("/api/v1/pr/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == mock_pr.title


# --- 2. SUBMIT & CANCEL TESTS ---

@pytest.mark.anyio
@patch.object(PRRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(PRRepository, "update", new_callable=AsyncMock)
@patch.object(BudgetCodeRepository, "get_by_code", new_callable=AsyncMock)
@patch.object(BudgetAllocationRepository, "get_by_budget_code_id", new_callable=AsyncMock)
@patch.object(BudgetReservationRepository, "create", new_callable=AsyncMock)
@patch.object(ApprovalWorkflowRepository, "create", new_callable=AsyncMock)
@patch.object(ApprovalStepRepository, "create", new_callable=AsyncMock)
@patch.object(WorkflowHistoryRepository, "create", new_callable=AsyncMock)
async def test_submit_pr_success(
    mock_wf_hist,
    mock_step_create,
    mock_wf_create,
    mock_res_create,
    mock_alloc_get,
    mock_bc_get,
    mock_pr_update,
    mock_get_pr,
    authenticate_user,
    async_client: AsyncClient,
    override_db,
    mock_pr,
    mock_budget_code
):
    mock_bc_get.return_value = mock_budget_code
    mock_alloc_get.return_value = None
    mock_get_pr.return_value = mock_pr

    def execute_side_effect(query):
        res = MagicMock()
        query_str = str(query)
        if "FROM roles" in query_str:
            if "role_id" in query_str:
                mock_role = MagicMock()
                mock_role.role_name = "Manager"
                res.scalar_one_or_none.return_value = mock_role
            else:
                res.scalar_one_or_none.return_value = None
        else:
            res.scalars().all.return_value = []
            res.scalar_one_or_none.return_value = None
        return res
    
    override_db.execute = AsyncMock(side_effect=execute_side_effect)

    response = await async_client.post("/api/v1/pr/1/submit")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Pending Manager Approval"


@pytest.mark.anyio
@patch.object(PRRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(PRRepository, "update", new_callable=AsyncMock)
@patch.object(BudgetReservationRepository, "get_by_pr_id", new_callable=AsyncMock)
@patch.object(BudgetCodeRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(BudgetAllocationRepository, "get_by_budget_code_id", new_callable=AsyncMock)
@patch.object(BudgetCodeRepository, "update", new_callable=AsyncMock)
@patch.object(ApprovalWorkflowRepository, "get_by_pr_id", new_callable=AsyncMock)
@patch.object(ApprovalWorkflowRepository, "update", new_callable=AsyncMock)
@patch.object(ApprovalStepRepository, "get_active_step_for_workflow", new_callable=AsyncMock)
@patch.object(ApprovalStepRepository, "update", new_callable=AsyncMock)
@patch.object(WorkflowHistoryRepository, "create", new_callable=AsyncMock)
async def test_cancel_pr(
    mock_wf_hist,
    mock_step_update,
    mock_active_step,
    mock_wf_update,
    mock_wf_get,
    mock_bc_update,
    mock_alloc_get,
    mock_bc_get,
    mock_res_get,
    mock_pr_update,
    mock_get_pr,
    authenticate_user,
    async_client: AsyncClient,
    override_db,
    mock_pr,
    mock_budget_code
):
    mock_pr.status = "Pending Manager Approval"
    mock_get_pr.return_value = mock_pr

    mock_res = BudgetReservation(reservation_id=1, pr_id=1, budget_code_id=1, reserved_amount=Decimal("4000.00"), status="Reserved")
    mock_res_get.return_value = [mock_res]

    mock_bc_get.return_value = mock_budget_code
    mock_alloc_get.return_value = None

    mock_wf = ApprovalWorkflow(workflow_id=1, pr_id=1, status="Under Review")
    mock_wf_get.return_value = mock_wf

    mock_step = ApprovalStep(step_id=1, workflow_id=1, status="Pending")
    mock_active_step.return_value = mock_step

    response = await async_client.post("/api/v1/pr/1/cancel")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Cancelled"


# --- 3. APPROVAL FLOW ACTIONS ---

@pytest.mark.anyio
@patch("src.api.approvals.get_current_user")
@patch.object(PRRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(PRRepository, "update", new_callable=AsyncMock)
@patch.object(BudgetReservationRepository, "get_by_pr_id", new_callable=AsyncMock)
@patch.object(ApprovalWorkflowRepository, "get_by_pr_id", new_callable=AsyncMock)
@patch.object(ApprovalWorkflowRepository, "update", new_callable=AsyncMock)
@patch.object(ApprovalStepRepository, "get_active_step_for_workflow", new_callable=AsyncMock)
@patch.object(ApprovalStepRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(ApprovalStepRepository, "update", new_callable=AsyncMock)
@patch.object(ApprovalHistoryRepository, "create", new_callable=AsyncMock)
@patch.object(WorkflowHistoryRepository, "create", new_callable=AsyncMock)
@patch("src.services.rfq_service.RFQService")
async def test_approve_step_success(
    mock_rfq_service_class,
    mock_wf_hist,
    mock_app_hist,
    mock_step_update,
    mock_step_get,
    mock_active_step,
    mock_wf_update,
    mock_wf_get,
    mock_res_get,
    mock_pr_update,
    mock_pr_get,
    mock_current_user,
    manager_jwt,
    mock_manager,
    async_client: AsyncClient,
    override_db,
    mock_pr
):
    mock_res_get.return_value = []
    mock_current_user.return_value = mock_manager
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_manager

    mock_rfq_instance = AsyncMock()
    mock_rfq_instance.create_rfq.return_value = MagicMock(rfq_id=1)
    mock_rfq_service_class.return_value = mock_rfq_instance

    mock_pr.status = "Pending Manager Approval"
    mock_pr_get.return_value = mock_pr

    mock_wf = ApprovalWorkflow(workflow_id=1, pr_id=1, status="Under Review")
    mock_wf_get.return_value = mock_wf

    # Pending Level 1 Manager Step
    mock_step = ApprovalStep(step_id=1, workflow_id=1, step_number=1, approver_role_id=2, status="Pending")
    mock_active_step.side_effect = [mock_step, mock_step, None] # First call: route handler, second call: service verification, third call: next step
    mock_step_get.return_value = mock_step

    def execute_side_effect(query):
        res = MagicMock()
        query_str = str(query)
        if "approval_workflows" in query_str:
            res.scalar_one_or_none.return_value = mock_wf
        elif "purchase_requisitions" in query_str:
            res.scalar_one_or_none.return_value = mock_pr
        elif "FROM users" in query_str:
            mock_requestor = MagicMock()
            mock_requestor.manager_id = 2
            res.scalar_one_or_none.return_value = mock_requestor
        elif "FROM roles" in query_str:
            if "role_id" in query_str:
                mock_role = MagicMock()
                mock_role.role_id = 2
                res.scalar_one_or_none.return_value = mock_role
            else:
                res.scalar_one_or_none.return_value = None
        else:
            res.scalars().first.return_value = None
            res.scalar_one_or_none.return_value = None
        return res
    override_db.execute.side_effect = execute_side_effect

    headers = {"Authorization": f"Bearer {manager_jwt}"}
    response = await async_client.post("/api/v1/pr/1/approve", json={"comments": "Looks good"}, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Approved"

    # Cleanup overrides
    app.dependency_overrides.pop(get_current_user, None)


# --- 4. COMMENTS & ATTACHMENTS TESTS ---

@pytest.mark.anyio
@patch.object(PRRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(CommentRepository, "create", new_callable=AsyncMock)
async def test_create_comment(
    mock_comment_create,
    mock_get_pr,
    authenticate_user,
    async_client: AsyncClient,
    override_db,
    mock_pr
):
    mock_get_pr.return_value = mock_pr
    mock_comment = ApprovalComment(
        comment_id=1, pr_id=1, user_id=1, content="This is a test comment", is_internal=False, created_at=datetime.now(timezone.utc)
    )
    mock_comment_create.return_value = mock_comment

    response = await async_client.post(
        "/api/v1/pr/1/comments",
        json={"content": "This is a test comment", "is_internal": False}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["content"] == "This is a test comment"


@pytest.mark.anyio
@patch.object(PRRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(PRAttachmentRepository, "create", new_callable=AsyncMock)
async def test_create_attachment(
    mock_attach_create,
    mock_get_pr,
    authenticate_user,
    async_client: AsyncClient,
    override_db,
    mock_pr
):
    mock_get_pr.return_value = mock_pr
    mock_attachment = PRAttachment(
        attachment_id=1, pr_id=1, file_name="specs.pdf", file_path="/uploads/specs.pdf", file_type="pdf", file_size=1024, uploaded_by=1, created_at=datetime.now(timezone.utc)
    )
    mock_attach_create.return_value = mock_attachment

    response = await async_client.post(
        "/api/v1/pr/1/attachments",
        json={"file_name": "specs.pdf", "file_path": "/uploads/specs.pdf", "file_type": "pdf", "file_size": 1024}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["file_name"] == "specs.pdf"
