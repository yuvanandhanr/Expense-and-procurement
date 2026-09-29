from datetime import timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.organization import BudgetCode, CostCenter, Department, Designation, OrgSettings
from src.repositories.organization import (
    BudgetCodeRepository,
    CostCenterRepository,
    DepartmentRepository,
    DesignationRepository,
    OrgSettingsRepository,
)
from src.schemas.organization import (
    BudgetCodeCreate,
    BudgetCodeUpdate,
    CostCenterCreate,
    CostCenterUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    DesignationCreate,
    DesignationUpdate,
    OrgSettingsUpdate,
)


class DepartmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = DepartmentRepository(session)

    async def create_department(self, data: DepartmentCreate) -> Department:
        existing = await self.repo.get_by_code(data.department_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with code {data.department_code} already exists."
            )
        dept = Department(
            department_name=data.department_name,
            department_code=data.department_code,
            description=data.description,
            status=data.status
        )
        return await self.repo.create(dept)

    async def get_department(self, dept_id: int) -> Department:
        dept = await self.repo.get_by_id(dept_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {dept_id} not found."
            )
        return dept

    async def list_departments(self, skip: int = 0, limit: int = 100) -> List[Department]:
        return await self.repo.list_all(skip=skip, limit=limit)

    async def update_department(self, dept_id: int, data: DepartmentUpdate) -> Department:
        dept = await self.get_department(dept_id)
        if data.department_name is not None:
            dept.department_name = data.department_name
        if data.department_code is not None:
            # check uniqueness if code changed
            if data.department_code != dept.department_code:
                existing = await self.repo.get_by_code(data.department_code)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Department with code {data.department_code} already exists."
                    )
            dept.department_code = data.department_code
        if data.description is not None:
            dept.description = data.description
        if data.status is not None:
            dept.status = data.status
        return await self.repo.update(dept)

    async def delete_department(self, dept_id: int) -> None:
        dept = await self.get_department(dept_id)
        await self.repo.delete(dept)


class DesignationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = DesignationRepository(session)

    async def create_designation(self, data: DesignationCreate) -> Designation:
        existing = await self.repo.get_by_name(data.designation_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Designation with name '{data.designation_name}' already exists."
            )
        desig = Designation(
            designation_name=data.designation_name,
            description=data.description,
            status=data.status
        )
        return await self.repo.create(desig)

    async def get_designation(self, desig_id: int) -> Designation:
        desig = await self.repo.get_by_id(desig_id)
        if not desig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Designation with ID {desig_id} not found."
            )
        return desig

    async def list_designations(self, skip: int = 0, limit: int = 100) -> List[Designation]:
        return await self.repo.list_all(skip=skip, limit=limit)

    async def update_designation(self, desig_id: int, data: DesignationUpdate) -> Designation:
        desig = await self.get_designation(desig_id)
        if data.designation_name is not None:
            if data.designation_name != desig.designation_name:
                existing = await self.repo.get_by_name(data.designation_name)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Designation with name '{data.designation_name}' already exists."
                    )
            desig.designation_name = data.designation_name
        if data.description is not None:
            desig.description = data.description
        if data.status is not None:
            desig.status = data.status
        return await self.repo.update(desig)

    async def delete_designation(self, desig_id: int) -> None:
        desig = await self.get_designation(desig_id)
        await self.repo.delete(desig)


class CostCenterService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CostCenterRepository(session)
        self.dept_repo = DepartmentRepository(session)

    async def create_cost_center(self, data: CostCenterCreate) -> CostCenter:
        existing = await self.repo.get_by_name(data.cost_center_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cost center with name '{data.cost_center_name}' already exists."
            )
        if data.department_id:
            dept = await self.dept_repo.get_by_id(data.department_id)
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Department with ID {data.department_id} does not exist."
                )
        cc = CostCenter(
            cost_center_name=data.cost_center_name,
            department_id=data.department_id,
            budget_limit=data.budget_limit,
            status=data.status
        )
        return await self.repo.create(cc)

    async def get_cost_center(self, cc_id: int) -> CostCenter:
        cc = await self.repo.get_by_id(cc_id)
        if not cc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cost center with ID {cc_id} not found."
            )
        return cc

    async def list_cost_centers(self, skip: int = 0, limit: int = 100) -> List[CostCenter]:
        return await self.repo.list_all(skip=skip, limit=limit)

    async def update_cost_center(self, cc_id: int, data: CostCenterUpdate) -> CostCenter:
        cc = await self.get_cost_center(cc_id)
        if data.cost_center_name is not None:
            if data.cost_center_name != cc.cost_center_name:
                existing = await self.repo.get_by_name(data.cost_center_name)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cost center with name '{data.cost_center_name}' already exists."
                    )
            cc.cost_center_name = data.cost_center_name
        if data.department_id is not None:
            if data.department_id:
                dept = await self.dept_repo.get_by_id(data.department_id)
                if not dept:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Department with ID {data.department_id} does not exist."
                    )
            cc.department_id = data.department_id
        if data.budget_limit is not None:
            cc.budget_limit = data.budget_limit
        if data.status is not None:
            cc.status = data.status
        return await self.repo.update(cc)

    async def delete_cost_center(self, cc_id: int) -> None:
        cc = await self.get_cost_center(cc_id)
        await self.repo.delete(cc)


class BudgetCodeService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = BudgetCodeRepository(session)
        self.dept_repo = DepartmentRepository(session)
        self.cc_repo = CostCenterRepository(session)

    async def create_budget_code(self, data: BudgetCodeCreate) -> BudgetCode:
        existing = await self.repo.get_by_code(data.budget_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Budget code '{data.budget_code}' already exists."
            )
        if data.department_id:
            dept = await self.dept_repo.get_by_id(data.department_id)
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Department with ID {data.department_id} does not exist."
                )
        if data.cost_center_id:
            cc = await self.cc_repo.get_by_id(data.cost_center_id)
            if not cc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cost center with ID {data.cost_center_id} does not exist."
                )
        bc = BudgetCode(
            budget_code=data.budget_code,
            description=data.description,
            department_id=data.department_id,
            cost_center_id=data.cost_center_id,
            annual_budget=data.annual_budget,
            available_budget=data.available_budget,
            fiscal_year=data.fiscal_year,
            status=data.status
        )
        return await self.repo.create(bc)

    async def get_budget_code(self, bc_id: int) -> BudgetCode:
        bc = await self.repo.get_by_id(bc_id)
        if not bc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget code with ID {bc_id} not found."
            )
        return bc

    async def list_budget_codes(self, skip: int = 0, limit: int = 100) -> List[BudgetCode]:
        return await self.repo.list_all(skip=skip, limit=limit)

    async def update_budget_code(self, bc_id: int, data: BudgetCodeUpdate) -> BudgetCode:
        bc = await self.get_budget_code(bc_id)
        if data.budget_code is not None:
            if data.budget_code != bc.budget_code:
                existing = await self.repo.get_by_code(data.budget_code)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Budget code '{data.budget_code}' already exists."
                    )
            bc.budget_code = data.budget_code
        if data.description is not None:
            bc.description = data.description
        if data.department_id is not None:
            if data.department_id:
                dept = await self.dept_repo.get_by_id(data.department_id)
                if not dept:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Department with ID {data.department_id} does not exist."
                    )
            bc.department_id = data.department_id
        if data.cost_center_id is not None:
            if data.cost_center_id:
                cc = await self.cc_repo.get_by_id(data.cost_center_id)
                if not cc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cost center with ID {data.cost_center_id} does not exist."
                    )
            bc.cost_center_id = data.cost_center_id
        if data.annual_budget is not None:
            bc.annual_budget = data.annual_budget
        if data.available_budget is not None:
            bc.available_budget = data.available_budget
        if data.fiscal_year is not None:
            bc.fiscal_year = data.fiscal_year
        if data.status is not None:
            bc.status = data.status
        return await self.repo.update(bc)

    async def delete_budget_code(self, bc_id: int) -> None:
        bc = await self.get_budget_code(bc_id)
        await self.repo.delete(bc)


class OrgSettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = OrgSettingsRepository(session)

    async def get_settings(self) -> OrgSettings:
        settings = await self.repo.get_latest()
        if not settings:
            # Seed default settings if empty
            settings = OrgSettings(
                org_name="Enterprise Platform",
                currency="USD",
                timezone="UTC",
                session_timeout_minutes=30
            )
            settings = await self.repo.create(settings)
        return settings

    async def update_settings(self, data: OrgSettingsUpdate) -> OrgSettings:
        settings = await self.get_settings()
        if data.org_name is not None:
            settings.org_name = data.org_name
        if data.currency is not None:
            settings.currency = data.currency
        if data.timezone is not None:
            settings.timezone = data.timezone
        if data.fiscal_year_start is not None:
            settings.fiscal_year_start = data.fiscal_year_start
        if data.fiscal_year_end is not None:
            settings.fiscal_year_end = data.fiscal_year_end
        if data.approval_thresholds is not None:
            settings.approval_thresholds = data.approval_thresholds
        if data.password_policy is not None:
            settings.password_policy = data.password_policy
        if data.session_timeout_minutes is not None:
            settings.session_timeout_minutes = data.session_timeout_minutes
        if data.logo_url is not None:
            settings.logo_url = data.logo_url
        return await self.repo.update(settings)
