"""
Pytest Configuration.

Sets up test clients, test environments, and dependency override fixtures
for validating the FastAPI application skeleton.
"""

import sys
from unittest.mock import MagicMock
# Mock pandas to bypass Windows Application Control blocking pandas DLLs
sys.modules['pandas'] = MagicMock()

from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Specifies asyncio backend for anyio/pytest tests.
    """
    return "asyncio"


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    Synchronous TestClient fixture.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous HTTPX test client using ASGITransport mapping to the FastAPI app.
    """
    # Use ASGITransport for modern HTTPX async testing
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """
    Mocks a SQLAlchemy AsyncSession for isolating connection checks.
    """
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.close = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def override_db(mock_db_session: AsyncMock) -> Generator[AsyncMock, None, None]:
    """
    Overrides get_db_session dependency in the FastAPI application with a mock session.
    """
    async def _get_db_override():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = _get_db_override
    yield mock_db_session
    app.dependency_overrides.pop(get_db_session, None)


from unittest.mock import patch, MagicMock as MockMagicMock, AsyncMock as MockAsyncMock

class MockerFixture:
    def __init__(self):
        self._patches = []
        self.AsyncMock = MockAsyncMock
        self.MagicMock = MockMagicMock

    def patch(self, *args, **kwargs):
        p = patch(*args, **kwargs)
        mocked = p.start()
        self._patches.append(p)
        return mocked

    def stopall(self):
        for p in reversed(self._patches):
            p.stop()

@pytest.fixture
def mocker():
    m = MockerFixture()
    yield m
    m.stopall()


from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.sqltypes import BigInteger
from src.database.base import Base
import src.models  # Ensure all models are registered in metadata

@compiles(BigInteger, "sqlite")
def compile_big_int_sqlite(type_, compiler, **kw):
    return "INTEGER"


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    In-memory SQLite async session fixture for database-level integration tests.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def setup_test_users(db_session: AsyncSession):
    """
    Fixture creating basic roles and users for testing approval and workflow constraints.
    """
    from src.models.auth import User, Role
    from src.models.organization import Department
    
    dept = Department(department_id=1, department_code="ENG", department_name="Engineering")
    db_session.add(dept)
    
    emp_role = Role(role_id=1, role_name="Employee", status=True)
    mgr_role = Role(role_id=2, role_name="Manager", status=True)
    admin_role = Role(role_id=3, role_name="Admin", status=True)
    fm_role = Role(role_id=4, role_name="Finance Manager", status=True)
    cfo_role = Role(role_id=5, role_name="CFO", status=True)
    db_session.add_all([emp_role, mgr_role, admin_role, fm_role, cfo_role])
    await db_session.commit()
    
    emp_user = User(
        user_id=1,
        employee_code="EMP001",
        first_name="Employee",
        last_name="User",
        email="emp@example.com",
        status="Active",
        department_id=1,
        roles=[emp_role]
    )
    mgr_user = User(
        user_id=2,
        employee_code="MGR001",
        first_name="Manager",
        last_name="User",
        email="mgr@example.com",
        status="Active",
        department_id=1,
        roles=[mgr_role]
    )
    admin_user = User(
        user_id=3,
        employee_code="ADM001",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        status="Active",
        department_id=1,
        roles=[admin_role]
    )
    db_session.add_all([emp_user, mgr_user, admin_user])
    await db_session.commit()
    await db_session.refresh(emp_user)
    await db_session.refresh(mgr_user)
    await db_session.refresh(admin_user)
    
    return {
        "employee": emp_user,
        "manager": mgr_user,
        "admin": admin_user,
    }


