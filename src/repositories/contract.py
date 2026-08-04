from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.contract import (
    Contract,
    ContractDocument,
    SubscriptionContract,
    AMCContract,
    RateContract,
)
from src.repositories.base import BaseRepository


class ContractRepository(BaseRepository[Contract]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Contract, session)

    async def get_by_id(self, entity_id: int) -> Optional[Contract]:
        query = (
            select(self.model)
            .where(self.model.contract_id == entity_id)
            .options(
                selectinload(self.model.documents),
                selectinload(self.model.subscription_details),
                selectinload(self.model.amc_details),
                selectinload(self.model.rate_details)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, contract_number: str) -> Optional[Contract]:
        query = select(self.model).where(self.model.contract_number == contract_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class ContractDocumentRepository(BaseRepository[ContractDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ContractDocument, session)

    async def get_by_id(self, entity_id: int) -> Optional[ContractDocument]:
        return await self.session.get(self.model, entity_id)


class SubscriptionContractRepository(BaseRepository[SubscriptionContract]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SubscriptionContract, session)

    async def get_by_id(self, entity_id: int) -> Optional[SubscriptionContract]:
        return await self.session.get(self.model, entity_id)


class AMCContractRepository(BaseRepository[AMCContract]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AMCContract, session)

    async def get_by_id(self, entity_id: int) -> Optional[AMCContract]:
        return await self.session.get(self.model, entity_id)


class RateContractRepository(BaseRepository[RateContract]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RateContract, session)

    async def get_by_id(self, entity_id: int) -> Optional[RateContract]:
        return await self.session.get(self.model, entity_id)

    async def find_rate_contract_for_item(self, item_name: str) -> Optional[RateContract]:
        query = (
            select(self.model)
            .join(self.model.contract)
            .where(self.model.item_name == item_name, Contract.status == "Active")
            .options(selectinload(self.model.contract))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
