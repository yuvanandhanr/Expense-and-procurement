from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.vendor import (
    Vendor,
    VendorContact,
    VendorDocument,
    VendorCategory,
    VendorPerformance,
    VendorBlacklist,
)
from src.repositories.base import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Vendor, session)

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Vendor]:
        query = (
            select(self.model)
            .options(
                selectinload(self.model.contacts),
                selectinload(self.model.documents),
                selectinload(self.model.categories),
                selectinload(self.model.performance),
                selectinload(self.model.blacklist_records)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, entity_id: int) -> Optional[Vendor]:
        query = (
            select(self.model)
            .where(self.model.vendor_id == entity_id)
            .options(
                selectinload(self.model.contacts),
                selectinload(self.model.documents),
                selectinload(self.model.categories),
                selectinload(self.model.performance),
                selectinload(self.model.blacklist_records)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, vendor_code: str) -> Optional[Vendor]:
        query = select(self.model).where(self.model.vendor_code == vendor_code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class VendorContactRepository(BaseRepository[VendorContact]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VendorContact, session)

    async def get_by_id(self, entity_id: int) -> Optional[VendorContact]:
        return await self.session.get(self.model, entity_id)

    async def list_by_vendor(self, vendor_id: int) -> List[VendorContact]:
        query = select(self.model).where(self.model.vendor_id == vendor_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class VendorDocumentRepository(BaseRepository[VendorDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VendorDocument, session)

    async def get_by_id(self, entity_id: int) -> Optional[VendorDocument]:
        return await self.session.get(self.model, entity_id)

    async def list_by_vendor(self, vendor_id: int) -> List[VendorDocument]:
        query = select(self.model).where(self.model.vendor_id == vendor_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class VendorCategoryRepository(BaseRepository[VendorCategory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VendorCategory, session)

    async def get_by_id(self, entity_id: int) -> Optional[VendorCategory]:
        return await self.session.get(self.model, entity_id)


class VendorPerformanceRepository(BaseRepository[VendorPerformance]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VendorPerformance, session)

    async def get_by_id(self, entity_id: int) -> Optional[VendorPerformance]:
        return await self.session.get(self.model, entity_id)

    async def get_by_vendor(self, vendor_id: int) -> Optional[VendorPerformance]:
        query = select(self.model).where(self.model.vendor_id == vendor_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class VendorBlacklistRepository(BaseRepository[VendorBlacklist]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VendorBlacklist, session)

    async def get_by_id(self, entity_id: int) -> Optional[VendorBlacklist]:
        return await self.session.get(self.model, entity_id)
