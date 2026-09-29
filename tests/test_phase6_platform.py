import io
import pytest
from datetime import timezone, datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from src.main import app
from src.auth.dependencies import get_current_user, JWTBearer, RoleChecker
from src.models.auth import User, Role
from src.models.platform_services import Notification, NotificationPreference, Attachment, SystemSetting, AuditLog, SearchIndex
from src.database.dependency import get_db_session


# --- Mock Users & Roles ---

@pytest.fixture
def mock_employee() -> User:
    role = Role(role_id=1, role_name="Employee", status=True)
    return User(
        user_id=1,
        employee_code="EMP001",
        first_name="Employee",
        last_name="One",
        email="employee@example.com",
        status="Active",
        roles=[role]
    )


@pytest.fixture
def mock_ceo() -> User:
    role = Role(role_id=2, role_name="CEO", status=True)
    return User(
        user_id=2,
        employee_code="CEO001",
        first_name="Chief",
        last_name="Exec",
        email="ceo@example.com",
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


# --- Test Dashboard Router ---

def test_dashboard_employee_success(client: TestClient, override_db: AsyncMock, mock_employee) -> None:
    async def _current_user_override():
        return mock_employee

    async def _jwt_override():
        return {"sub": "1"}

    app.dependency_overrides[get_current_user] = _current_user_override
    app.dependency_overrides[JWTBearer] = _jwt_override

    # Mock dashboard service data
    with patch("src.services.dashboard_service.DashboardService.get_dashboard_data", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {
            "role": "Employee",
            "timestamp": "2026-08-04T12:00:00",
            "widgets": {"my_purchase_requests": {"Draft": 1}}
        }

        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "Employee"
        assert "my_purchase_requests" in data["widgets"]

    # Clear overrides
    app.dependency_overrides.clear()


# --- Test Analytics Router & RBAC ---

def test_analytics_spend_ceo_allowed(client: TestClient, override_db: AsyncMock, mock_ceo) -> None:
    async def _current_user_override():
        return mock_ceo

    app.dependency_overrides[get_current_user] = _current_user_override

    with patch("src.services.dashboard_service.DashboardService.get_spend_analytics", new_callable=AsyncMock) as mock_spend:
        mock_spend.return_value = {"department_spend": [], "vendor_spend": []}

        response = client.get("/api/v1/analytics/spend")
        assert response.status_code == 200
        assert "department_spend" in response.json()

    app.dependency_overrides.clear()


def test_analytics_spend_employee_forbidden(client: TestClient, override_db: AsyncMock, mock_employee) -> None:
    async def _current_user_override():
        return mock_employee

    app.dependency_overrides[get_current_user] = _current_user_override

    response = client.get("/api/v1/analytics/spend")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    app.dependency_overrides.clear()


# --- Test Reports Router ---

def test_generate_report_success(client: TestClient, override_db: AsyncMock, mock_employee) -> None:
    async def _current_user_override():
        return mock_employee
    app.dependency_overrides[get_current_user] = _current_user_override

    with patch("src.services.report_service.ReportService.generate_report_file", new_callable=AsyncMock) as mock_gen:
        from src.models.platform_services import Report
        mock_gen.return_value = Report(
            report_id=10,
            name="Spend Export",
            report_type="PR",
            created_by=1,
            file_path="reports/test.csv",
            file_type="CSV",
            status="Completed",
            created_at=datetime.utcnow()
        )

        response = client.post(
            "/api/v1/reports/generate",
            json={"name": "Spend Export", "report_type": "PR", "file_type": "CSV"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report_id"] == 10
        assert data["status"] == "Completed"

    app.dependency_overrides.clear()


# --- Test Notifications Router ---

def test_list_notifications(client: TestClient, override_db: AsyncMock, mock_employee) -> None:
    async def _current_user_override():
        return mock_employee
    app.dependency_overrides[get_current_user] = _current_user_override

    with patch("src.repositories.platform_services.NotificationRepository.list_by_user", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            Notification(
                notification_id=1,
                user_id=1,
                title="PR Status Update",
                message="PR-123 is Approved",
                notification_type="In-App",
                status="Unread",
                created_at=datetime.utcnow()
            )
        ]

        response = client.get("/api/v1/notifications")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["notification_id"] == 1

    app.dependency_overrides.clear()


# --- Test Audit Logs Router ---

def test_get_audit_logs_rbac_success(client: TestClient, override_db: AsyncMock, mock_ceo) -> None:
    async def _current_user_override():
        return mock_ceo
    app.dependency_overrides[get_current_user] = _current_user_override

    with patch("src.repositories.platform_services.AuditLogRepository.list_logs", new_callable=AsyncMock) as mock_logs:
        mock_logs.return_value = [
            AuditLog(
                audit_log_id=1,
                timestamp=datetime.utcnow(),
                user_email="ceo@example.com",
                action="Login",
                module="auth"
            )
        ]

        response = client.get("/api/v1/audit")
        assert response.status_code == 200
        assert len(response.json()) == 1

    app.dependency_overrides.clear()


# --- Test Search Router ---

def test_global_search_success(client: TestClient, override_db: AsyncMock, mock_employee) -> None:
    async def _current_user_override():
        return mock_employee
    app.dependency_overrides[get_current_user] = _current_user_override

    with patch("src.services.search_service.SearchService.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            {
                "index_id": 1,
                "entity_type": "Vendor",
                "entity_id": "5",
                "title": "Vendor Acme",
                "content": "Acme Corp",
                "meta_data": None,
                "updated_at": "2026-08-04T12:00:00"
            }
        ]

        response = client.get("/api/v1/search?q=Acme")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["entity_type"] == "Vendor"

    app.dependency_overrides.clear()


# --- Test Files Upload Router ---

def test_file_upload_validation_failure(client: TestClient, override_db: AsyncMock, mock_employee) -> None:
    async def _current_user_override():
        return mock_employee
    app.dependency_overrides[get_current_user] = _current_user_override

    # Test uploading an executable file (invalid extension and signature)
    response = client.post(
        "/api/v1/files/upload",
        data={"entity_type": "PR", "entity_id": "1", "category": "Purchase Attachments"},
        files={"file": ("malicious.exe", b"MZ\x90\x00...", "application/x-msdownload")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "extension" in response.json()["detail"]

    # Test invalid magic numbers (PDF filename, but doesn't start with %PDF)
    response = client.post(
        "/api/v1/files/upload",
        data={"entity_type": "PR", "entity_id": "1", "category": "Purchase Attachments"},
        files={"file": ("test.pdf", b"NOTAPDF...", "application/pdf")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "signature" in response.json()["detail"]

    app.dependency_overrides.clear()


# --- Test System Settings Router ---

def test_settings_admin_only(client: TestClient, override_db: AsyncMock, mock_admin) -> None:
    async def _current_user_override():
        return mock_admin
    app.dependency_overrides[get_current_user] = _current_user_override

    with patch("src.services.setting_service.SettingService.list_settings", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            SystemSetting(
                setting_id=1,
                key="org_name",
                value="Enterprise Corp",
                category="Organization"
            )
        ]

        response = client.get("/api/v1/settings/system")
        assert response.status_code == 200
        assert len(response.json()) == 1

    app.dependency_overrides.clear()


# --- Test System Monitoring Router ---

def test_system_health_checks(client: TestClient, override_db: AsyncMock, mock_employee) -> None:
    async def _current_user_override():
        return mock_employee
    app.dependency_overrides[get_current_user] = _current_user_override

    with patch("src.services.monitoring_service.MonitoringService.perform_system_health_check", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = {
            "status": "Healthy",
            "checked_at": "2026-08-04T12:00:00",
            "components": {"database": {"status": "Healthy"}}
        }

        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        assert response.json()["status"] == "Healthy"

    app.dependency_overrides.clear()
