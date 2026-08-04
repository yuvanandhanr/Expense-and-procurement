from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.organization import BudgetCode, CostCenter, Department, Designation, OrgSettings
from src.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    """
    Repository for Department CRUD data access operations.
    """
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Department, session)

    async def get_by_id(self, entity_id: int) -> Optional[Department]:
        """
        Retrieves a department by integer ID.
        """
        return await self.session.get(self.model, entity_id)

    async def get_by_code(self, department_code: str) -> Optional[Department]:
        """
        Retrieves a department by unique business code.
        """
        query = select(self.model).where(self.model.department_code == department_code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class DesignationRepository(BaseRepository[Designation]):
    """
    Repository for Designation CRUD data access operations.
    """
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Designation, session)

    async def get_by_id(self, entity_id: int) -> Optional[Designation]:
        """
        Retrieves a designation by integer ID.
        """
        return await self.session.get(self.model, entity_id)

    async def get_by_name(self, designation_name: str) -> Optional[Designation]:
        """
        Retrieves a designation by unique name.
        """
        query = select(self.model).where(self.model.designation_name == designation_name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class CostCenterRepository(BaseRepository[CostCenter]):
    """
    Repository for CostCenter CRUD data access operations.
    """
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CostCenter, session)

    async def get_by_id(self, entity_id: int) -> Optional[CostCenter]:
        """
        Retrieves a cost center by integer ID.
        """
        return await self.session.get(self.model, entity_id)

    async def get_by_name(self, cost_center_name: str) -> Optional[CostCenter]:
        """
        Retrieves a cost center by unique name.
        """
        query = select(self.model).where(self.model.cost_center_name == cost_center_name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class BudgetCodeRepository(BaseRepository[BudgetCode]):
    """
    Repository for BudgetCode CRUD data access operations.
    """
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(BudgetCode, session)

    async def get_by_id(self, entity_id: int) -> Optional[BudgetCode]:
        """
        Retrieves a budget code by integer ID.
        """
        return await self.session.get(self.model, entity_id)

    async def get_by_code(self, budget_code: str) -> Optional[BudgetCode]:
        """
        Retrieves a budget code by unique string identifier.
        """
        query = select(self.model).where(self.model.budget_code == budget_code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class OrgSettingsRepository(BaseRepository[OrgSettings]):
    """
    Repository for OrgSettings CRUD data access operations.
    """
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(OrgSettings, session)

    async def get_by_id(self, entity_id: int) -> Optional[OrgSettings]:
        """
        Retrieves setting by ID.
        """
        return await self.session.get(self.model, entity_id)

    async def get_latest(self) -> Optional[OrgSettings]:
        """
        Retrieves the latest configuration settings.
        """
        query = select(self.model).order_by(self.model.settings_id.desc()).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
