from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.attachment import PRAttachment
from src.repositories.base import BaseRepository


class PRAttachmentRepository(BaseRepository[PRAttachment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PRAttachment, session)

    async def get_by_id(self, entity_id: int) -> Optional[PRAttachment]:
        return await self.session.get(self.model, entity_id)

    async def list_by_pr_id(self, pr_id: int) -> List[PRAttachment]:
        query = select(self.model).where(self.model.pr_id == pr_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
