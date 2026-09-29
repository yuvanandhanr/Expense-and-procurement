import uuid
import hashlib
from datetime import timezone, datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import jwt
import pytest
from fastapi import status
from httpx import AsyncClient
from argon2 import PasswordHasher
from src.core.config import settings
from src.models.auth import User, Role, Permission, LoginSession, RefreshToken
from src.models.organization import Department, Designation, CostCenter, BudgetCode, OrgSettings
from src.repositories.auth import UserRepository, SessionRepository, RefreshTokenRepository, RoleRepository, PermissionRepository
from src.repositories.organization import DepartmentRepository, DesignationRepository, CostCenterRepository, BudgetCodeRepository, OrgSettingsRepository

ph = PasswordHasher()


@pytest.fixture
def test_hashed_password() -> str:
    return ph.hash("securepassword")


@pytest.fixture
def mock_user(test_hashed_password) -> User:
    permission_view = Permission(
        permission_id=1,
        permission_name="users.view",
        module_name="users",
        created_at=datetime.utcnow()
    )
    permission_create = Permission(
        permission_id=2,
        permission_name="users.create",
        module_name="users",
        created_at=datetime.utcnow()
    )
    permission_update = Permission(
        permission_id=3,
        permission_name="users.update",
        module_name="users",
        created_at=datetime.utcnow()
    )
    permission_delete = Permission(
        permission_id=4,
        permission_name="users.delete",
        module_name="users",
        created_at=datetime.utcnow()
    )
    permission_settings = Permission(
        permission_id=5,
        permission_name="admin.settings",
        module_name="admin",
        created_at=datetime.utcnow()
    )
    
    role_admin = Role(
        role_id=1,
        role_name="Admin",
        status=True,
        created_at=datetime.utcnow()
    )
    role_admin.permissions = [permission_view, permission_create, permission_update, permission_delete, permission_settings]

    user = User(
        user_id=1,
        employee_code="EMP001",
        first_name="John",
        last_name="Doe",
        email="employee@example.com",
        password_hash=test_hashed_password,
        designation="Manager",
        employment_type="Full-Time",
        status="Active",
        failed_login_attempts=0,
        is_locked=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user.roles = [role_admin]
    return user


@pytest.fixture
def valid_jwt(mock_user) -> str:
    payload = {
        "sub": str(mock_user.user_id),
        "email": mock_user.email,
        "exp": 9999999999
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def mock_session() -> LoginSession:
    return LoginSession(
        session_id=10,
        user_id=1,
        status="Active",
        login_time=datetime.utcnow()
    )


@pytest.fixture
def authenticate_user(mock_user):
    """
    FastAPI dependency overrides to authenticate requests automatically.
    """
    async def _get_current_user_override():
        return mock_user

    async def _jwt_bearer_override():
        return {"sub": str(mock_user.user_id), "email": mock_user.email}

    from src.main import app
    from src.auth.dependencies import get_current_user, JWTBearer

    app.dependency_overrides[get_current_user] = _get_current_user_override
    app.dependency_overrides[JWTBearer] = _jwt_bearer_override
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(JWTBearer, None)


# --- AUTHENTICATION & LOGIN TESTS ---

@pytest.mark.anyio
@patch("src.services.auth_service.verify_google_id_token", new_callable=AsyncMock)
@patch.object(UserRepository, "get_by_email", new_callable=AsyncMock)
@patch.object(UserRepository, "update", new_callable=AsyncMock)
@patch.object(SessionRepository, "create", new_callable=AsyncMock)
@patch.object(RefreshTokenRepository, "create", new_callable=AsyncMock)
async def test_google_login_success(
    mock_rt_create,
    mock_session_create,
    mock_user_update,
    mock_get_by_email,
    mock_verify,
    async_client: AsyncClient,
    override_db,
    mock_user
):
    mock_verify.return_value = {
        "email": "employee@dataeko.ai",
        "email_verified": True,
        "sub": "google12345",
        "given_name": "John",
        "family_name": "Doe",
        "picture": "https://example.com/john.jpg"
    }
    mock_user.email = "employee@dataeko.ai"
    mock_get_by_email.return_value = mock_user

    response = await async_client.post(
        "/api/v1/auth/google",
        json={"credential": "valid_token"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


@pytest.mark.anyio
@patch("src.services.auth_service.verify_google_id_token", new_callable=AsyncMock)
async def test_google_login_invalid_domain(
    mock_verify,
    async_client: AsyncClient,
    override_db
):
    mock_verify.return_value = {
        "email": "employee@gmail.com",
        "email_verified": True,
        "sub": "google12345",
        "given_name": "John",
        "family_name": "Doe"
    }
    response = await async_client.post(
        "/api/v1/auth/google",
        json={"credential": "invalid_domain_token"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Only DataEko employees can login."


@pytest.mark.anyio
@patch("src.services.auth_service.EmailService")
@patch("src.services.auth_service.OTPRequestRepository")
async def test_vendor_otp_request_success(
    mock_otp_repo_class,
    mock_email_service_class,
    async_client: AsyncClient,
    override_db
):
    mock_vendor = MagicMock()
    mock_vendor.status = "Active"
    mock_vendor.email = "supplier@example.com"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_vendor
    override_db.execute = AsyncMock(return_value=mock_result)

    mock_otp_repo_class.return_value.create = AsyncMock()
    
    mock_email_instance = mock_email_service_class.return_value
    mock_email_instance.template_repo.get_by_name = AsyncMock(return_value=MagicMock())
    mock_email_instance.create_template_if_not_exists = AsyncMock()
    mock_email_instance.queue_email = AsyncMock(return_value=MagicMock())
    mock_email_instance.send_email_immediately = AsyncMock(return_value=True)

    response = await async_client.post(
        "/api/v1/auth/vendor/otp-request",
        json={"email": "supplier@example.com"}
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.anyio
@patch.object(UserRepository, "get_by_email", new_callable=AsyncMock)
@patch.object(UserRepository, "create", new_callable=AsyncMock)
@patch.object(SessionRepository, "create", new_callable=AsyncMock)
@patch.object(RefreshTokenRepository, "create", new_callable=AsyncMock)
async def test_vendor_otp_verify_success(
    mock_rt_create,
    mock_session_create,
    mock_user_create,
    mock_get_by_email,
    async_client: AsyncClient,
    override_db,
    mock_user
):
    import pyotp
    mock_vendor = MagicMock()
    mock_vendor.vendor_id = 10
    mock_vendor.vendor_code = "VND10"
    mock_vendor.vendor_name = "Mock Supplier"
    mock_vendor.mfa_secret = pyotp.random_base32()
    mock_vendor.mfa_enabled = True
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_vendor
    override_db.execute = AsyncMock(return_value=mock_result)

    mock_get_by_email.return_value = mock_user
    
    valid_otp = pyotp.TOTP(mock_vendor.mfa_secret).now()

    response = await async_client.post(
        "/api/v1/auth/vendor/otp-verify",
        json={"email": "supplier@example.com", "otp": valid_otp}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


@pytest.mark.anyio
async def test_vendor_otp_verify_invalid(
    async_client: AsyncClient,
    override_db
):
    import pyotp
    mock_vendor = MagicMock()
    mock_vendor.mfa_secret = pyotp.random_base32()
    mock_vendor.mfa_enabled = True
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_vendor
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.post(
        "/api/v1/auth/vendor/otp-verify",
        json={"email": "supplier@example.com", "otp": "000000"} # Invalid OTP
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid Authenticator code."


# --- LOGOUT & REFRESH TESTS ---

@pytest.mark.anyio
@patch("src.auth.dependencies.SessionRepository")
@patch("src.auth.dependencies.UserRepository")
@patch("src.services.auth_service.SessionRepository")
@patch("src.services.auth_service.RefreshTokenRepository")
async def test_logout_success(
    mock_rt_repo_class,
    mock_auth_session_repo_class,
    mock_dep_user_repo_class,
    mock_dep_session_repo_class,
    async_client: AsyncClient,
    override_db,
    valid_jwt,
    mock_user,
    mock_session
):
    # Mock dependency instances
    mock_dep_session_repo_class.return_value.get_active_session_by_token = AsyncMock(return_value=mock_session)
    mock_dep_user_repo_class.return_value.get_by_id = AsyncMock(return_value=mock_user)
    
    # Mock database execute to return empty list of refresh tokens to revoke
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    override_db.execute = AsyncMock(return_value=mock_result)

    # Mock authentication service instances
    mock_auth_session_repo_class.return_value.get_active_session_by_token = AsyncMock(return_value=mock_session)
    mock_auth_session_repo_class.return_value.update = AsyncMock()
    mock_rt_repo_class.return_value.update = AsyncMock()

    headers = {"Authorization": f"Bearer {valid_jwt}"}
    response = await async_client.post("/api/v1/auth/logout", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Successfully logged out"


@pytest.mark.anyio
@patch.object(RefreshTokenRepository, "get_by_token", new_callable=AsyncMock)
@patch.object(RefreshTokenRepository, "update", new_callable=AsyncMock)
@patch.object(UserRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(RefreshTokenRepository, "create", new_callable=AsyncMock)
@patch.object(SessionRepository, "create", new_callable=AsyncMock)
async def test_refresh_token_success(
    mock_session_create,
    mock_rt_create,
    mock_get_user,
    mock_rt_update,
    mock_get_rt,
    async_client: AsyncClient,
    override_db,
    mock_user
):
    mock_rt = RefreshToken(
        token_id=1,
        user_id=1,
        token="old_refresh_token",
        expires_at=datetime.utcnow() + timedelta(days=2),
        is_expired=False
    )
    mock_get_rt.return_value = mock_rt
    mock_get_user.return_value = mock_user

    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "old_refresh_token"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


# --- PASSWORD FORGOT & RESET TESTS ---

@pytest.mark.anyio
@patch.object(UserRepository, "get_by_email", new_callable=AsyncMock)
async def test_forgot_password(
    mock_get_email,
    async_client: AsyncClient,
    override_db,
    mock_user
):
    mock_get_email.return_value = mock_user
    response = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "employee@example.com"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.json()


@pytest.mark.anyio
async def test_reset_password(
    async_client: AsyncClient,
    override_db,
    mock_user
):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    override_db.execute = AsyncMock(return_value=mock_result)

    response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": "reset_token_hex_example", "new_password": "newsecurepassword123"}
    )
    assert response.status_code == status.HTTP_200_OK


# --- USER CRUD TESTS ---

@pytest.mark.anyio
@patch.object(UserRepository, "get_by_email", new_callable=AsyncMock)
@patch.object(UserRepository, "create", new_callable=AsyncMock)
async def test_create_user(
    mock_create,
    mock_get_email,
    authenticate_user,
    async_client: AsyncClient,
    override_db,
    mock_user
):
    mock_get_email.return_value = None
    mock_create.return_value = mock_user

    response = await async_client.post(
        "/api/v1/users",
        json={
            "employee_code": "EMP002",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "password": "alicepassword123"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.anyio
@patch.object(UserRepository, "get_by_id", new_callable=AsyncMock)
async def test_get_user(
    mock_get_user,
    authenticate_user,
    async_client: AsyncClient,
    override_db,
    mock_user
):
    mock_get_user.return_value = mock_user

    response = await async_client.get("/api/v1/users/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == mock_user.email


# --- ORGANIZATION DEPARTMENTS CRUD ---

@pytest.mark.anyio
@patch.object(DepartmentRepository, "get_by_code", new_callable=AsyncMock)
@patch.object(DepartmentRepository, "create", new_callable=AsyncMock)
async def test_create_department(
    mock_dept_create,
    mock_get_code,
    authenticate_user,
    async_client: AsyncClient,
    override_db
):
    mock_get_code.return_value = None
    mock_dept = Department(
        department_id=1,
        department_name="Engineering",
        department_code="ENG",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_dept_create.return_value = mock_dept

    response = await async_client.post(
        "/api/v1/departments",
        json={"department_name": "Engineering", "department_code": "ENG"}
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.anyio
@patch.object(DepartmentRepository, "list_all", new_callable=AsyncMock)
async def test_list_departments(
    mock_list,
    authenticate_user,
    async_client: AsyncClient,
    override_db
):
    mock_list.return_value = [
        Department(
            department_id=1,
            department_name="Engineering",
            department_code="ENG",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]

    response = await async_client.get("/api/v1/departments")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


# --- COST CENTRES CRUD ---

@pytest.mark.anyio
@patch.object(CostCenterRepository, "get_by_name", new_callable=AsyncMock)
@patch.object(CostCenterRepository, "create", new_callable=AsyncMock)
async def test_create_cost_center(
    mock_cc_create,
    mock_get_name,
    authenticate_user,
    async_client: AsyncClient,
    override_db
):
    mock_get_name.return_value = None
    mock_cc = CostCenter(
        cost_center_id=1,
        cost_center_name="Cloud Hosting",
        budget_limit=50000.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_cc_create.return_value = mock_cc

    response = await async_client.post(
        "/api/v1/cost_centres",
        json={"cost_center_name": "Cloud Hosting", "budget_limit": 50000.0}
    )
    assert response.status_code == status.HTTP_201_CREATED


# --- BUDGET CODES CRUD ---

@pytest.mark.anyio
@patch.object(BudgetCodeRepository, "get_by_code", new_callable=AsyncMock)
@patch.object(BudgetCodeRepository, "create", new_callable=AsyncMock)
async def test_create_budget_code(
    mock_bc_create,
    mock_get_code,
    authenticate_user,
    async_client: AsyncClient,
    override_db
):
    mock_get_code.return_value = None
    mock_bc = BudgetCode(
        budget_code_id=1,
        budget_code="BC-CLOUD-01",
        annual_budget=120000.0,
        available_budget=120000.0,
        fiscal_year="FY2026",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_bc_create.return_value = mock_bc

    response = await async_client.post(
        "/api/v1/budget_codes",
        json={
            "budget_code": "BC-CLOUD-01",
            "annual_budget": 120000.0,
            "available_budget": 120000.0,
            "fiscal_year": "FY2026"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED


# --- ROLES CRUD ---

@pytest.mark.anyio
@patch.object(RoleRepository, "get_by_name", new_callable=AsyncMock)
@patch.object(RoleRepository, "create", new_callable=AsyncMock)
async def test_create_role(
    mock_role_create,
    mock_get_name,
    authenticate_user,
    async_client: AsyncClient,
    override_db
):
    mock_get_name.return_value = None
    mock_role = Role(
        role_id=2,
        role_name="CFO",
        status=True,
        created_at=datetime.utcnow()
    )
    mock_role_create.return_value = mock_role

    response = await async_client.post(
        "/api/v1/roles",
        json={"role_name": "CFO", "description": "Chief Financial Officer"}
    )
    assert response.status_code == status.HTTP_201_CREATED


# --- PERMISSIONS CRUD ---

@pytest.mark.anyio
@patch.object(PermissionRepository, "get_by_name", new_callable=AsyncMock)
@patch.object(PermissionRepository, "create", new_callable=AsyncMock)
async def test_create_permission(
    mock_perm_create,
    mock_get_name,
    authenticate_user,
    async_client: AsyncClient,
    override_db
):
    mock_get_name.return_value = None
    mock_perm = Permission(
        permission_id=3,
        permission_name="invoice.approve",
        module_name="invoices",
        created_at=datetime.utcnow()
    )
    mock_perm_create.return_value = mock_perm

    response = await async_client.post(
        "/api/v1/permissions",
        json={"permission_name": "invoice.approve", "module_name": "invoices"}
    )
    assert response.status_code == status.HTTP_201_CREATED


# --- ORG SETTINGS GET & PUT ---

@pytest.mark.anyio
@patch.object(OrgSettingsRepository, "get_latest", new_callable=AsyncMock)
async def test_get_settings(
    mock_latest,
    authenticate_user,
    async_client: AsyncClient,
    override_db
):
    mock_latest.return_value = OrgSettings(
        settings_id=1,
        org_name="Enterprise Test Inc",
        currency="USD",
        timezone="UTC",
        session_timeout_minutes=30,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    response = await async_client.get("/api/v1/settings")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["org_name"] == "Enterprise Test Inc"


# --- ERROR & ACCESS CONTROL STATES ---

@pytest.mark.anyio
async def test_get_me_unauthorized_missing_token(
    async_client: AsyncClient,
    override_db
):
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
@patch("src.auth.dependencies.SessionRepository")
async def test_get_me_revoked_session(
    mock_dep_session_repo_class,
    async_client: AsyncClient,
    override_db,
    valid_jwt
):
    mock_dep_session_repo_class.return_value.get_active_session_by_token = AsyncMock(return_value=None)

    headers = {"Authorization": f"Bearer {valid_jwt}"}
    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
