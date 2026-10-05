import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from httpx import AsyncClient
from decimal import Decimal
from datetime import date

from src.models.auth import User, Role
from src.models.assets import Asset, AssetIncident, AssetCategory

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
def mock_manager() -> User:
    role = Role(role_id=2, role_name="Manager", status=True)
    return User(
        user_id=2,
        employee_code="MGR001",
        email="mgr@example.com",
        status="Active",
        roles=[role],
        department_id=1
    )

@pytest.fixture
def mock_it() -> User:
    role = Role(role_id=3, role_name="Admin", status=True)
    return User(
        user_id=3,
        employee_code="IT001",
        email="it@example.com",
        status="Active",
        roles=[role]
    )

@pytest.fixture
def mock_asset() -> Asset:
    return Asset(
        asset_id=10,
        asset_tag="AST-100",
        assigned_employee_id=1,
        department_id=1,
        status="Assigned",
        assignments=[]
    )

@pytest.fixture
def authenticate_employee(mock_employee):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_employee
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def authenticate_manager(mock_manager):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_manager
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def authenticate_it(mock_it):
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_it
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.anyio
async def test_report_incident(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock,
    mock_asset
):
    mock_incident = AssetIncident(
        incident_id=1,
        asset_id=10,
        reporter_id=1,
        description="Screen cracked",
        incident_type="Damage",
        status="Submitted",
        incident_date=date.today(),
        asset=mock_asset
    )

    mock_asset_result = MagicMock()
    mock_asset_result.scalar_one_or_none.return_value = mock_asset

    mock_incident_result = MagicMock()
    mock_incident_result.scalar_one.return_value = mock_incident
    mock_incident_result.scalar_one_or_none.return_value = mock_incident

    override_db.execute = AsyncMock(side_effect=[mock_asset_result, mock_incident_result])

    async def mock_refresh(instance):
        instance.incident_id = 1
        instance.incident_date = date.today()
        instance.description = "Screen cracked"
        instance.incident_type = "Damage"
        instance.status = "Submitted"
        instance.asset = mock_asset

    override_db.refresh = AsyncMock(side_effect=mock_refresh)

    response = await async_client.post(
        "/api/v1/asset-incidents",
        json={
            "asset_id": 10,
            "description": "Screen cracked",
            "incident_type": "Damage"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["asset_id"] == 10
    assert data["incident_type"] == "Damage"
    assert data["status"] == "Submitted"


@pytest.mark.anyio
async def test_manager_approve_incident(
    authenticate_manager,
    async_client: AsyncClient,
    override_db: AsyncMock,
    mock_asset
):
    mock_incident = AssetIncident(
        incident_id=1,
        asset_id=10,
        reporter_id=1,
        description="Screen cracked",
        incident_type="Damage",
        status="Submitted",
        incident_date=date.today(),
        asset=mock_asset
    )

    mock_result_initial = MagicMock()
    mock_result_initial.scalar_one_or_none.return_value = mock_incident

    mock_result_reload = MagicMock()
    mock_result_reload.scalar_one.return_value = mock_incident
    mock_result_reload.scalar_one_or_none.return_value = mock_incident

    override_db.execute = AsyncMock(side_effect=[mock_result_initial, mock_result_reload])

    response = await async_client.post(
        "/api/v1/asset-incidents/1/action",
        json={
            "action": "Approve",
            "manager_inspection_assessment": "Needs repair or replacement",
            "manager_inspection_comments": "Please inspect physically"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Manager Approved"


@pytest.mark.anyio
async def test_manager_reject_incident(
    authenticate_manager,
    async_client: AsyncClient,
    override_db: AsyncMock,
    mock_asset
):
    mock_incident = AssetIncident(
        incident_id=2,
        asset_id=10,
        reporter_id=1,
        description="Screen cracked",
        incident_type="Damage",
        status="Submitted",
        incident_date=date.today(),
        asset=mock_asset
    )

    mock_result_initial = MagicMock()
    mock_result_initial.scalar_one_or_none.return_value = mock_incident

    mock_result_reload = MagicMock()
    mock_result_reload.scalar_one.return_value = mock_incident
    mock_result_reload.scalar_one_or_none.return_value = mock_incident

    override_db.execute = AsyncMock(side_effect=[mock_result_initial, mock_result_reload])

    response = await async_client.post(
        "/api/v1/asset-incidents/2/action",
        json={
            "action": "Reject",
            "resolution": "Not a damage"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Rejected"
    assert mock_incident.asset.status == "Assigned"


@pytest.mark.anyio
@patch("src.api.asset_incidents.PRService", autospec=True)
async def test_it_replace_incident(
    mock_pr_service_cls,
    authenticate_it,
    async_client: AsyncClient,
    override_db: AsyncMock,
    mock_asset
):
    mock_incident = AssetIncident(
        incident_id=1,
        asset_id=10,
        reporter_id=1,
        description="Screen cracked",
        incident_type="Damage",
        status="Admin Approved",
        incident_date=date.today(),
        asset=mock_asset
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    
    mock_avail_result = MagicMock()
    mock_avail_result.scalars.return_value.first.return_value = None

    mock_cat_result = MagicMock()
    mock_cat_result.scalar_one_or_none.return_value = AssetCategory(category_id=1, category_name="Hardware")

    mock_reload_result = MagicMock()
    mock_reload_result.scalar_one.return_value = mock_incident
    mock_reload_result.scalar_one_or_none.return_value = mock_incident
    
    override_db.execute = AsyncMock(side_effect=[mock_result, mock_avail_result, mock_cat_result, mock_reload_result])
    
    # Mock PR Service
    mock_pr_service_inst = mock_pr_service_cls.return_value
    mock_new_pr = MagicMock()
    mock_new_pr.pr_id = 99
    mock_pr_service_inst.create_pr = AsyncMock(return_value=mock_new_pr)
    mock_pr_service_inst.submit_pr = AsyncMock()

    response = await async_client.post(
        "/api/v1/asset-incidents/1/action",
        json={
            "action": "Assign Replacement",
            "resolution": "Unrepairable, need new unit"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Waiting for Procurement"
    assert response.json()["linked_pr_id"] == 99

