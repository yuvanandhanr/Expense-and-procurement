"""
Base Repository Module.

Establishes the BaseRepository class utilizing SQLAlchemy 2.0 select syntax
for generic asynchronous CRUD database access patterns.
"""

import uuid
from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.base import Base

# Type variable constrained to SQLAlchemy models inheriting from Declarative Base
ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic Asynchronous Repository Base.
    
    Provides standard database operations for entities inheriting from Base.
    """

    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        """
        Initializes the repository with a specific model class and DB session.
        """
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[ModelT]:
        """
        Retrieves an entity by its UUID primary key.
        """
        query = select(self.model).where(self.model.id == entity_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelT]:
        """
        Retrieves a paginated list of all entities.
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, entity: ModelT) -> ModelT:
        """
        Saves a new entity in the database.
        
        Requires a session flush to auto-generate database-managed properties (e.g. IDs).
        """
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        """
        Marks an entity as dirty and flushes the changes.
        """
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        """
        Removes an entity from the database.
        """
        await self.session.delete(entity)
        await self.session.flush()
