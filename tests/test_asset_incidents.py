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


@pytest.mark.anyio
async def test_report_incident_as_draft(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock,
    mock_asset
):
    mock_incident = AssetIncident(
        incident_id=5,
        asset_id=10,
        reporter_id=1,
        description="Keyboard key stuck",
        incident_type="Malfunctioning",
        status="Draft",
        incident_date=date.today(),
        asset=mock_asset
    )

    mock_asset_result = MagicMock()
    mock_asset_result.scalar_one_or_none.return_value = mock_asset

    mock_incident_result = MagicMock()
    mock_incident_result.scalar_one.return_value = mock_incident
    mock_incident_result.scalar_one_or_none.return_value = mock_incident

    override_db.execute = AsyncMock(side_effect=[mock_asset_result, mock_incident_result])

    response = await async_client.post(
        "/api/v1/asset-incidents",
        json={
            "asset_id": 10,
            "description": "Keyboard key stuck",
            "incident_type": "Malfunctioning",
            "is_draft": True
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "Draft"


@pytest.mark.anyio
async def test_edit_draft_incident_with_submit(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock,
    mock_asset
):
    mock_incident = AssetIncident(
        incident_id=6,
        asset_id=10,
        reporter_id=1,
        description="Draft issue",
        incident_type="Damaged",
        status="Draft",
        incident_date=date.today(),
        asset=mock_asset
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident

    override_db.execute = AsyncMock(return_value=mock_result)

    async def mock_refresh(instance):
        instance.status = "Reported"

    override_db.refresh = AsyncMock(side_effect=mock_refresh)

    response = await async_client.put(
        "/api/v1/asset-incidents/6",
        json={
            "description": "Updated issue ready for review",
            "is_draft": False
        }
    )

    assert response.status_code == status.HTTP_200_OK
    assert mock_incident.status == "Reported"


@pytest.mark.anyio
async def test_submit_draft_incident_endpoint(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock,
    mock_asset
):
    mock_incident = AssetIncident(
        incident_id=7,
        asset_id=10,
        reporter_id=1,
        description="Draft issue",
        incident_type="Damaged",
        status="Draft",
        incident_date=date.today(),
        asset=mock_asset
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident

    override_db.execute = AsyncMock(return_value=mock_result)

    async def mock_refresh(instance):
        instance.status = "Reported"

    override_db.refresh = AsyncMock(side_effect=mock_refresh)

    response = await async_client.post("/api/v1/asset-incidents/7/submit")
    assert response.status_code == status.HTTP_200_OK
    assert mock_incident.status == "Reported"


@pytest.mark.anyio
async def test_cannot_edit_submitted_incident(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock,
    mock_asset
):
    mock_incident = AssetIncident(
        incident_id=8,
        asset_id=10,
        reporter_id=1,
        description="Submitted issue",
        incident_type="Damaged",
        status="Reported",
        incident_date=date.today(),
        asset=mock_asset
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.put(
        "/api/v1/asset-incidents/8",
        json={"description": "Attempt to edit"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Incident reports cannot be edited once submitted" in response.json()["detail"]


@pytest.mark.anyio
async def test_delete_draft_incident(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock
):
    mock_incident = AssetIncident(
        incident_id=9,
        asset_id=10,
        reporter_id=1,
        description="Draft to delete",
        incident_type="Damaged",
        status="Draft"
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.delete("/api/v1/asset-incidents/9")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    override_db.delete.assert_awaited_once_with(mock_incident)


@pytest.mark.anyio
async def test_cannot_delete_submitted_incident(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock
):
    mock_incident = AssetIncident(
        incident_id=10,
        asset_id=10,
        reporter_id=1,
        description="Reported incident",
        incident_type="Damaged",
        status="Reported"
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.delete("/api/v1/asset-incidents/10")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only draft incident reports can be deleted" in response.json()["detail"]


@pytest.mark.anyio
async def test_non_owner_cannot_delete_draft_incident(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock
):
    mock_incident = AssetIncident(
        incident_id=11,
        asset_id=10,
        reporter_id=999,  # Different user
        description="Other user draft",
        incident_type="Damaged",
        status="Draft"
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.delete("/api/v1/asset-incidents/11")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_non_owner_cannot_view_draft_incident(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock
):
    mock_incident = AssetIncident(
        incident_id=12,
        asset_id=10,
        reporter_id=999,  # Different user
        description="Other user draft",
        incident_type="Damaged",
        status="Draft"
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.get("/api/v1/asset-incidents/12")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Draft incident reports are only visible to the owner" in response.json()["detail"]


@pytest.mark.anyio
async def test_list_incidents_filters_other_users_drafts(
    authenticate_employee,
    async_client: AsyncClient,
    override_db: AsyncMock
):
    my_draft = AssetIncident(
        incident_id=13,
        asset_id=10,
        reporter_id=1,  # current user
        description="My draft",
        incident_type="Damaged",
        status="Draft"
    )
    other_draft = AssetIncident(
        incident_id=14,
        asset_id=10,
        reporter_id=999,  # other user
        description="Other draft",
        incident_type="Damaged",
        status="Draft"
    )
    other_reported = AssetIncident(
        incident_id=15,
        asset_id=10,
        reporter_id=999,
        description="Other reported",
        incident_type="Damaged",
        status="Reported"
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [my_draft, other_draft, other_reported]
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.get("/api/v1/asset-incidents")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    incident_ids = [item["incident_id"] for item in items]
    assert 13 in incident_ids
    assert 14 not in incident_ids  # other user's draft excluded
    assert 15 in incident_ids



