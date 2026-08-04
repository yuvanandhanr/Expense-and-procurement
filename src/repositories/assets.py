from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.assets import (
    AssetCategory,
    Asset,
    AssetAssignment,
    AssetHistory,
    AssetDocument,
)
from src.repositories.base import BaseRepository


class AssetCategoryRepository(BaseRepository[AssetCategory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AssetCategory, session)

    async def get_by_id(self, entity_id: int) -> Optional[AssetCategory]:
        return await self.session.get(self.model, entity_id)

    async def get_by_name(self, name: str) -> Optional[AssetCategory]:
        query = select(self.model).where(self.model.category_name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class AssetRepository(BaseRepository[Asset]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Asset, session)

    async def get_by_id(self, entity_id: int) -> Optional[Asset]:
        query = (
            select(self.model)
            .where(self.model.asset_id == entity_id)
            .options(
                selectinload(self.model.assignments),
                selectinload(self.model.history),
                selectinload(self.model.documents)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, asset_number: str) -> Optional[Asset]:
        query = select(self.model).where(self.model.asset_number == asset_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_tag(self, asset_tag: str) -> Optional[Asset]:
        query = select(self.model).where(self.model.asset_tag == asset_tag)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class AssetAssignmentRepository(BaseRepository[AssetAssignment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AssetAssignment, session)

    async def get_by_id(self, entity_id: int) -> Optional[AssetAssignment]:
        return await self.session.get(self.model, entity_id)

    async def get_active_assignment_for_asset(self, asset_id: int) -> Optional[AssetAssignment]:
        query = select(self.model).where(self.model.asset_id == asset_id, self.model.status == "Active")
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class AssetHistoryRepository(BaseRepository[AssetHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AssetHistory, session)

    async def get_by_id(self, entity_id: int) -> Optional[AssetHistory]:
        return await self.session.get(self.model, entity_id)


class AssetDocumentRepository(BaseRepository[AssetDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AssetDocument, session)

    async def get_by_id(self, entity_id: int) -> Optional[AssetDocument]:
        return await self.session.get(self.model, entity_id)
