import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, date
from decimal import Decimal

from src.models.auth import User, Role
from src.models.expense import ExpenseReport, Receipt, ExpenseApproval


@pytest.fixture
def mock_owner() -> User:
    role = Role(role_id=1, role_name="Employee", status=True)
    return User(
        user_id=10,
        employee_code="EMP010",
        first_name="Alice",
        email="alice@example.com",
        status="Active",
        roles=[role],
        manager_id=2
    )


@pytest.fixture
def mock_other_employee() -> User:
    role = Role(role_id=1, role_name="Employee", status=True)
    return User(
        user_id=99,
        employee_code="EMP099",
        first_name="Bob",
        email="bob@example.com",
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
        email="mgr@example.com",
        status="Active",
        roles=[role]
    )


@pytest.fixture
def mock_cfo() -> User:
    role = Role(role_id=5, role_name="CFO", status=True)
    return User(
        user_id=5,
        employee_code="CFO001",
        first_name="Chief",
        email="cfo@example.com",
        status="Active",
        roles=[role]
    )


@pytest.mark.anyio
async def test_owner_can_access_receipt_image(mock_owner, async_client: AsyncClient, mocker):
    from src.main import app
    from src.auth.dependencies import get_current_user
    from src.database.dependency import get_db_session

    app.dependency_overrides[get_current_user] = lambda: mock_owner

    mock_session = mocker.AsyncMock()
    app.dependency_overrides[get_db_session] = lambda: mock_session

    report = ExpenseReport(
        expense_report_id=1,
        employee_id=10,
        status="Pending Manager Approval",
        employee=mock_owner,
        approvals=[]
    )
    receipt = Receipt(
        receipt_id=1,
        expense_report_id=1,
        merchant_name="Starbucks",
        verified_amount=Decimal("15.50"),
        image_path="/uploads/receipts/test.png",
        file_name="receipt.png",
        expense_report=report,
        file_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )

    mocker.patch('src.api.expenses.ExpenseRepository.get_receipt_by_id', return_value=receipt)

    response = await async_client.get("/api/v1/expenses/receipts/1/image")
    assert response.status_code == status.HTTP_200_OK
    assert "image" in response.headers["content-type"]
    assert 'inline; filename="receipt.png"' in response.headers["content-disposition"]

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.anyio
async def test_unauthorized_user_denied_receipt_access(mock_other_employee, mock_owner, async_client: AsyncClient, mocker):
    from src.main import app
    from src.auth.dependencies import get_current_user
    from src.database.dependency import get_db_session

    app.dependency_overrides[get_current_user] = lambda: mock_other_employee

    mock_session = mocker.AsyncMock()
    app.dependency_overrides[get_db_session] = lambda: mock_session

    report = ExpenseReport(
        expense_report_id=1,
        employee_id=10,  # Owned by Alice (10)
        status="Pending Manager Approval",
        employee=mock_owner,
        approvals=[]
    )
    receipt = Receipt(
        receipt_id=1,
        expense_report_id=1,
        merchant_name="Starbucks",
        verified_amount=Decimal("15.50"),
        image_path="/uploads/receipts/test.png",
        file_name="receipt.png",
        expense_report=report
    )

    mocker.patch('src.api.expenses.ExpenseRepository.get_receipt_by_id', return_value=receipt)

    response = await async_client.get("/api/v1/expenses/receipts/1/image")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.anyio
async def test_manager_and_cfo_can_access_receipt_image(mock_manager, mock_cfo, mock_owner, async_client: AsyncClient, mocker):
    from src.main import app
    from src.auth.dependencies import get_current_user
    from src.database.dependency import get_db_session

    mock_session = mocker.AsyncMock()
    app.dependency_overrides[get_db_session] = lambda: mock_session

    report = ExpenseReport(
        expense_report_id=1,
        employee_id=10,
        status="Pending Manager Approval",
        employee=mock_owner,
        approvals=[]
    )
    receipt = Receipt(
        receipt_id=1,
        expense_report_id=1,
        merchant_name="Airline",
        verified_amount=Decimal("450.00"),
        image_path="/uploads/receipts/flight.pdf",
        file_name="flight.pdf",
        expense_report=report,
        file_data="JVBERi0xLjQKJcTl8uXrp/Og0MTGCjEgMCBvYmoKPDwKL1R5cGUgL0NhdGFsb2cKL1BhZ2VzIDIgMCBSCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9UeXBlIC9QYWdlcwovS2lkcyBbMyAwIFJdCi9Db3VudCAxCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9QYWdlCi9QYXJlbnQgMiAwIFIKL01lZGlhQm94IFswIDAgNjEyIDc5Ml0KPj4KZW5kb2JqCnhyZWYKMCA0CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAxNSAwMDAwMCBuIAowMDAwMDAwMDY4IDAwMDAwIG4gCjAwMDAwMDAxMTUgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA0Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgoyMDEKJSVFT0YK"
    )
    mocker.patch('src.api.expenses.ExpenseRepository.get_receipt_by_id', return_value=receipt)

    # 1. Manager of Alice
    app.dependency_overrides[get_current_user] = lambda: mock_manager
    res_mgr = await async_client.get("/api/v1/expenses/receipts/1/image")
    assert res_mgr.status_code == status.HTTP_200_OK

    # 2. CFO
    app.dependency_overrides[get_current_user] = lambda: mock_cfo
    res_cfo = await async_client.get("/api/v1/expenses/receipts/1/image")
    assert res_cfo.status_code == status.HTTP_200_OK

    # 3. Download endpoint
    res_dl = await async_client.get("/api/v1/expenses/receipts/1/download")
    assert res_dl.status_code == status.HTTP_200_OK
    assert "attachment" in res_dl.headers["content-disposition"]

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db_session, None)
