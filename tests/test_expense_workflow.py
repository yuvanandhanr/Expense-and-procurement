import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, date
from decimal import Decimal

from src.models.auth import User, Role
from src.models.expense import ExpenseReport, ExpenseApproval

@pytest.fixture
def mock_dept_manager() -> User:
    role = Role(role_id=2, role_name="Manager", status=True)
    return User(
        user_id=2,
        employee_code="MGR001",
        first_name="Manager",
        email="mgr@example.com",
        status="Active",
        roles=[role]
    )

@pytest.fixture
def mock_finance_manager() -> User:
    role = Role(role_id=4, role_name="Finance Manager", status=True)
    return User(
        user_id=4,
        employee_code="FM001",
        first_name="FinanceMgr",
        email="fm@example.com",
        status="Active",
        roles=[role]
    )

@pytest.fixture
def authenticate_dept_manager(mock_dept_manager):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_dept_manager
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def authenticate_finance_manager(mock_finance_manager):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_finance_manager
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.anyio
async def test_expense_approval_under_1000(
    authenticate_dept_manager,
    async_client: AsyncClient,
    mocker
):
    mock_session = mocker.AsyncMock()
    
    report = ExpenseReport(
        expense_report_id=1,
        employee_id=10,
        total_amount=Decimal("500.00"),
        status="Pending Manager Approval"
    )
    
    approval = ExpenseApproval(
        approval_id=1,
        expense_report_id=1,
        approver_id=2, # dept manager
        status="Pending"
    )
    
    mocker.patch('src.api.expenses.ExpenseRepository.get_report_by_id', return_value=report)
    
    res2 = mocker.MagicMock()
    res2.scalar_one_or_none.return_value = approval
    mock_session.execute.return_value = res2
    
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session
    
    response = await async_client.post(
        f"/api/v1/expenses/1/approve",
        json={"comments": "Looks good"}
    )
    
    print(response.json())
    assert response.status_code == status.HTTP_200_OK
    assert report.status == "Payment Requested"
    assert report.payment_status == "Pending Payment"
    assert approval.status == "Approved"
    
    app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.anyio
async def test_expense_approval_over_1000(
    authenticate_dept_manager,
    mock_finance_manager,
    async_client: AsyncClient,
    mocker
):
    mock_session = mocker.AsyncMock()
    
    report = ExpenseReport(
        expense_report_id=2,
        employee_id=10,
        total_amount=Decimal("1500.00"),
        status="Pending Manager Approval"
    )
    
    approval = ExpenseApproval(
        approval_id=2,
        expense_report_id=2,
        approver_id=2, # dept manager
        status="Pending"
    )
    
    mocker.patch('src.api.expenses.ExpenseRepository.get_report_by_id', return_value=report)
    
    def mock_execute(query):
        if "expense_approvals" in str(query):
            res = mocker.MagicMock()
            res.scalar_one_or_none.return_value = approval
            return res
        elif "users" in str(query):
            res = mocker.MagicMock()
            res.scalars().first.return_value = mock_finance_manager
            return res
        return mocker.MagicMock()
        
    mock_session.execute.side_effect = mock_execute
    mock_session.add = mocker.MagicMock()
    
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session
    
    response = await async_client.post(
        f"/api/v1/expenses/2/approve",
        json={"comments": "Looks good"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert report.status == "Pending Finance Manager Approval"
    assert approval.status == "Approved"
    
    # Verify FM approval created
    assert mock_session.add.called
    add_arg = mock_session.add.call_args[0][0]
    assert isinstance(add_arg, ExpenseApproval)
    assert add_arg.approver_id == mock_finance_manager.user_id
    
    app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.anyio
async def test_expense_finance_manager_approval(
    authenticate_finance_manager,
    async_client: AsyncClient,
    mocker
):
    mock_session = mocker.AsyncMock()
    
    report = ExpenseReport(
        expense_report_id=3,
        employee_id=10,
        total_amount=Decimal("1500.00"),
        status="Pending Finance Manager Approval"
    )
    
    approval = ExpenseApproval(
        approval_id=3,
        expense_report_id=3,
        approver_id=4, # finance manager
        status="Pending"
    )
    
    mocker.patch('src.api.expenses.ExpenseRepository.get_report_by_id', return_value=report)
    
    res2 = mocker.MagicMock()
    res2.scalar_one_or_none.return_value = approval
    mock_session.execute.return_value = res2
    
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session
    
    response = await async_client.post(
        f"/api/v1/expenses/3/approve",
        json={"comments": "Approved by Finance"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert report.status == "Payment Requested"
    assert report.payment_status == "Pending Payment"
    assert approval.status == "Approved"
    
    app.dependency_overrides.pop(get_db_session, None)

@pytest.fixture
def mock_employee() -> User:
    role = Role(role_id=1, role_name="Employee", status=True)
    return User(
        user_id=10,
        employee_code="EMP001",
        first_name="Employee",
        email="emp@example.com",
        status="Active",
        roles=[role],
        manager_id=2
    )

@pytest.fixture
def authenticate_employee(mock_employee):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_employee
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.anyio
async def test_expense_submit_employee(
    authenticate_employee,
    async_client: AsyncClient,
    mocker
):
    mock_session = mocker.AsyncMock()
    
    report = ExpenseReport(
        expense_report_id=4,
        employee_id=10,
        total_amount=Decimal("500.00"),
        status="Draft",
        justification=None,
        receipts=[]
    )
    
    mocker.patch('src.api.expenses.ExpenseRepository.get_report_by_id', return_value=report)
    mock_update = mocker.patch('src.api.expenses.ExpenseRepository.update_report')
    mocker.patch('src.services.approval_service.ApprovalService.initialize_approval_flow')
    
    def mock_execute(query):
        res = mocker.MagicMock()
        res.scalars().first.return_value = None
        return res
        
    mock_session.execute.side_effect = mock_execute
    
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session
    
    response = await async_client.post(f"/api/v1/expenses/4/submit")
    
    assert response.status_code == status.HTTP_200_OK
    assert report.status == "Pending Approval"
    mock_update.assert_called_with(report)
    
    app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.anyio
async def test_expense_submit_manager_missing_justification(
    authenticate_dept_manager,
    async_client: AsyncClient,
    mocker
):
    mock_session = mocker.AsyncMock()
    
    from src.models.expense import Receipt
    receipt = Receipt(
        verified_amount=Decimal("600.00"),
        merchant_name="Flight",
        receipt_date=date.today(),
        category=None # Will trigger policy flag
    )
    
    report = ExpenseReport(
        expense_report_id=5,
        employee_id=2, # manager
        total_amount=Decimal("600.00"),
        status="Draft",
        justification=None, # Missing justification
        receipts=[receipt]
    )
    
    mocker.patch('src.api.expenses.ExpenseRepository.get_report_by_id', return_value=report)
    
    def mock_execute(query):
        res = mocker.MagicMock()
        res.scalars().first.return_value = None
        return res
        
    mock_session.execute.side_effect = mock_execute
    
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session
    
    response = await async_client.post(f"/api/v1/expenses/5/submit")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Manager claims require justification" in response.json()["detail"]
    
    app.dependency_overrides.pop(get_db_session, None)
