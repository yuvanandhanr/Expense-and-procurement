import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import timezone, datetime, date

from src.models.auth import User, Role
from src.models.assets import Asset, AssetAssignment, AssetHistory
from src.models.offboarding import OffboardingTask

@pytest.fixture
def mock_admin() -> User:
    role = Role(role_id=3, role_name="Admin", status=True)
    return User(
        user_id=3,
        employee_code="ADM001",
        first_name="Alice",
        email="admin@example.com",
        status="Active",
        roles=[role]
    )

@pytest.fixture
def mock_employee_to_offboard() -> User:
    role = Role(role_id=1, role_name="Employee", status=True)
    return User(
        user_id=4,
        employee_code="EMP002",
        first_name="Bob",
        email="bob@example.com",
        status="Active",
        roles=[role]
    )

@pytest.fixture
def authenticate_admin(mock_admin):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.anyio
async def test_offboarding_trigger(
    authenticate_admin,
    async_client: AsyncClient,
    mock_employee_to_offboard,
    mocker
):
    # Setup mocks
    mock_session = mocker.AsyncMock()
    mock_session.get.return_value = mock_employee_to_offboard

    assignment = AssetAssignment(
        assignment_id=1,
        asset_id=100,
        assigned_to=4,
        status="Active",
        assigned_date=date.today()
    )
    
    mock_result = mocker.MagicMock()
    mock_result.scalars().all.return_value = [assignment]
    mock_session.execute.return_value = mock_result
    
    def mock_add(obj):
        obj.task_id = 99 if obj.task_type == "Retrieve Asset" else 100
        obj.status = "Pending"
        obj.created_at = datetime.utcnow()
    
    mock_session.add = mocker.MagicMock(side_effect=mock_add)
    
    # Mock get_db_session dependency
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session

    response = await async_client.post(f"/api/v1/offboarding/{mock_employee_to_offboard.user_id}/trigger")
    
    app.dependency_overrides.pop(get_db_session, None)
    
    assert response.status_code == status.HTTP_201_CREATED
    tasks = response.json()
    assert len(tasks) == 4
    assert any(t["task_type"] == "Manager Approval" for t in tasks)
    assert any(t["task_type"] == "Retrieve Asset" for t in tasks)
    assert any(t["task_type"] == "Revoke IT Access" for t in tasks)
    assert any(t["task_type"] == "Financial Clearance" for t in tasks)

@pytest.mark.anyio
async def test_offboarding_clear_and_finalize(
    authenticate_admin,
    async_client: AsyncClient,
    mock_employee_to_offboard,
    mocker
):
    # Setup mocks
    mock_session = mocker.AsyncMock()
    
    task = OffboardingTask(
        task_id=99,
        employee_id=4,
        asset_id=100,
        task_type="Retrieve Asset",
        status="Pending",
        notes="Please retrieve",
        created_at=datetime.utcnow()
    )
    
    asset = Asset(
        asset_id=100,
        status="Assigned"
    )
    
    assignment = AssetAssignment(
        assignment_id=1,
        asset_id=100,
        assigned_to=4,
        status="Active",
        assigned_date=date.today()
    )

    def mock_get(model, id):
        if model == OffboardingTask and id == 99:
            return task
        if model == Asset and id == 100:
            return asset
        if model == User and id == 4:
            return mock_employee_to_offboard
        return None
    mock_session.get.side_effect = mock_get
    mock_session.add = mocker.MagicMock()
    
    mock_result = mocker.MagicMock()
    mock_result.scalar_one_or_none.return_value = assignment
    # For finalize pending tasks check:
    mock_result2 = mocker.MagicMock()
    mock_result2.scalars().all.return_value = [] # No pending tasks
    
    mock_session.execute.side_effect = [mock_result, mock_result2]
    
    # Mock get_db_session dependency
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session

    # 1. Clear Task
    response = await async_client.post(
        f"/api/v1/offboarding/tasks/99/clear",
        json={"notes": "Laptop returned in good condition"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    cleared_task = response.json()
    assert cleared_task["status"] == "Cleared"
    assert "Laptop returned" in cleared_task["notes"]
    
    # Verify underlying models were modified correctly
    assert assignment.status == "Returned"
    assert asset.status == "Available"

    # 2. Finalize
    response_fin = await async_client.post(f"/api/v1/offboarding/4/finalize")
    assert response_fin.status_code == status.HTTP_200_OK
    assert mock_employee_to_offboard.status == "Inactive"
    
    app.dependency_overrides.pop(get_db_session, None)

@pytest.mark.anyio
async def test_offboarding_manager_reject(
    authenticate_admin,
    async_client: AsyncClient,
    mock_employee_to_offboard,
    mocker
):
    mock_session = mocker.AsyncMock()
    task = OffboardingTask(
        task_id=1,
        employee_id=4,
        task_type="Manager Approval",
        status="Pending",
        notes="Approve offboarding",
        created_at=datetime.utcnow()
    )

    def mock_get(model, id):
        if model == OffboardingTask and id == 1:
            return task
        if model == User and id == 4:
            return mock_employee_to_offboard
        return None
    
    mock_session.get.side_effect = mock_get
    mock_session.add = mocker.MagicMock()
    
    mock_result = mocker.MagicMock()
    mock_result.scalars().all.return_value = [task] # 1 rejected task
    mock_session.execute.return_value = mock_result
    
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session

    # Reject task
    response = await async_client.post(
        f"/api/v1/offboarding/tasks/1/clear",
        json={"notes": "Rejected offboarding", "action": "Reject"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    cleared_task = response.json()
    assert cleared_task["status"] == "Rejected"
    
    # Finalize should fail
    response_fin = await async_client.post(f"/api/v1/offboarding/4/finalize")
    assert response_fin.status_code == status.HTTP_400_BAD_REQUEST
    assert "pending, blocked or rejected" in response_fin.json()["detail"]
    
    app.dependency_overrides.pop(get_db_session, None)

@pytest.mark.anyio
async def test_offboarding_asset_damaged(
    authenticate_admin,
    async_client: AsyncClient,
    mock_employee_to_offboard,
    mocker
):
    mock_session = mocker.AsyncMock()
    task = OffboardingTask(
        task_id=2,
        employee_id=4,
        asset_id=100,
        task_type="Retrieve Asset",
        status="Pending",
        notes="Please retrieve",
        created_at=datetime.utcnow()
    )
    asset = Asset(asset_id=100, status="Assigned")
    assignment = AssetAssignment(
        assignment_id=1,
        asset_id=100,
        assigned_to=4,
        status="Active",
        assigned_date=date.today()
    )

    def mock_get(model, id):
        if model == OffboardingTask and id == 2:
            return task
        if model == Asset and id == 100:
            return asset
        return None
        
    mock_session.get.side_effect = mock_get
    mock_session.add = mocker.MagicMock()
    mock_result = mocker.MagicMock()
    mock_result.scalar_one_or_none.return_value = assignment
    mock_session.execute.return_value = mock_result
    
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session

    # Clear task with condition Damaged
    response = await async_client.post(
        f"/api/v1/offboarding/tasks/2/clear",
        json={"notes": "Screen cracked", "action": "Clear", "asset_condition": "Damaged"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert task.status == "Cleared"
    assert asset.status == "Damaged"
    
    # Check if AssetIncident and AssetHistory were added
    add_calls = mock_session.add.call_args_list
    assert len(add_calls) == 2
    from src.models.assets import AssetIncident
    assert isinstance(add_calls[0][0][0], AssetIncident)
    assert isinstance(add_calls[1][0][0], AssetHistory)
    
    app.dependency_overrides.pop(get_db_session, None)

@pytest.mark.anyio
async def test_offboarding_financial_pending_dues(
    authenticate_admin,
    async_client: AsyncClient,
    mock_employee_to_offboard,
    mocker
):
    mock_session = mocker.AsyncMock()
    task = OffboardingTask(
        task_id=3,
        employee_id=4,
        task_type="Financial Clearance",
        status="Pending",
        notes="Clear dues",
        created_at=datetime.utcnow()
    )

    def mock_get(model, id):
        if model == OffboardingTask and id == 3:
            return task
        if model == User and id == 4:
            return mock_employee_to_offboard
        return None
        
    mock_session.get.side_effect = mock_get
    
    mock_result = mocker.MagicMock()
    mock_result.scalars().all.return_value = [task] # 1 blocked task
    mock_session.execute.return_value = mock_result
    
    from src.main import app
    from src.database.dependency import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_session

    # Clear task with pending dues
    response = await async_client.post(
        f"/api/v1/offboarding/tasks/3/clear",
        json={"notes": "Needs to pay 50 dollars", "action": "Pending Dues"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Blocked"
    
    # Finalize should fail
    response_fin = await async_client.post(f"/api/v1/offboarding/4/finalize")
    assert response_fin.status_code == status.HTTP_400_BAD_REQUEST
    
    app.dependency_overrides.pop(get_db_session, None)
