from typing import List, Optional
from datetime import timezone, datetime, date, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.contract import (
    Contract,
    ContractDocument,
    SubscriptionContract,
    AMCContract,
    RateContract,
)
from src.repositories.contract import (
    ContractRepository,
    ContractDocumentRepository,
    SubscriptionContractRepository,
    AMCContractRepository,
    RateContractRepository,
)
from src.schemas.contract import ContractCreate, ContractUpdate


class ContractService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.contract_repo = ContractRepository(db)
        self.doc_repo = ContractDocumentRepository(db)
        self.sub_repo = SubscriptionContractRepository(db)
        self.amc_repo = AMCContractRepository(db)
        self.rate_repo = RateContractRepository(db)

    async def create_contract(self, data: ContractCreate) -> Contract:
        # Check duplicate
        existing = await self.contract_repo.get_by_number(data.contract_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract with number '{data.contract_number}' already exists"
            )

        contract = Contract(
            contract_number=data.contract_number,
            vendor_id=data.vendor_id,
            title=data.title,
            contract_type=data.contract_type,
            status="Active",
            start_date=data.start_date,
            end_date=data.end_date,
            renewal_date=data.renewal_date,
            expiry_reminder_date=data.expiry_reminder_date,
            created_at=datetime.now(timezone.utc)
        )
        contract = await self.contract_repo.create(contract)

        # Create Subscription details if applicable
        if data.contract_type == "subscription" and data.subscription_details:
            sub = SubscriptionContract(
                contract_id=contract.contract_id,
                license_count=data.subscription_details.license_count,
                billing_frequency=data.subscription_details.billing_frequency,
                unit_price=data.subscription_details.unit_price,
                auto_renew=data.subscription_details.auto_renew
            )
            await self.sub_repo.create(sub)

        # Create AMC details if applicable
        if data.contract_type == "annual_maintenance" and data.amc_details:
            amc = AMCContract(
                contract_id=contract.contract_id,
                coverage_details=data.amc_details.coverage_details,
                response_sla_hours=data.amc_details.response_sla_hours,
                scheduled_visits_count=data.amc_details.scheduled_visits_count
            )
            await self.amc_repo.create(amc)

        # Create Rate Contract details if applicable
        if data.contract_type == "rate_contract" and data.rate_details:
            for rate_data in data.rate_details:
                rate = RateContract(
                    contract_id=contract.contract_id,
                    item_name=rate_data.item_name,
                    specification=rate_data.specification,
                    pre_negotiated_unit_price=rate_data.pre_negotiated_unit_price
                )
                await self.rate_repo.create(rate)

        return await self.contract_repo.get_by_id(contract.contract_id)

    async def update_contract(self, contract_id: int, data: ContractUpdate) -> Contract:
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(contract, k, v)
        
        contract.updated_at = datetime.now(timezone.utc)
        await self.contract_repo.update(contract)
        return contract

    async def renew_subscription(self, contract_id: int, new_end_date: date, new_license_count: Optional[int] = None) -> Contract:
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract or contract.contract_type != "subscription":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active subscription contract not found")

        contract.end_date = new_end_date
        contract.renewal_date = new_end_date + timedelta(days=1)
        contract.status = "Active"
        await self.contract_repo.update(contract)

        if new_license_count is not None and contract.subscription_details:
            contract.subscription_details.license_count = new_license_count
            await self.sub_repo.update(contract.subscription_details)

        return await self.contract_repo.get_by_id(contract_id)

    async def check_expirations_and_reminders(self) -> List[Contract]:
        """
        Retrieves all AMC and Subscription contracts approaching renewal date.
        """
        from sqlalchemy import select, and_
        today = date.today()
        query = select(Contract).where(
            and_(
                Contract.status == "Active",
                Contract.expiry_reminder_date <= today,
                Contract.end_date >= today
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
