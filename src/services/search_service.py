import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.platform_services import SearchIndex
from src.models.auth import User
from src.models.purchase_requisition import PurchaseRequisition
from src.models.purchase_order import PurchaseOrder
from src.models.vendor import Vendor
from src.repositories.platform_services import SearchIndexRepository

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service managing global search capabilities and text indexing.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.search_repo = SearchIndexRepository(db)

    async def index_entity(
        self,
        entity_type: str,
        entity_id: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SearchIndex:
        """
        Creates or updates a text search index entry for a database record.
        """
        # Check if record is already indexed
        query = select(SearchIndex).where(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id
        )
        result = await self.db.execute(query)
        index_entry = result.scalar_one_or_none()

        meta_str = json.dumps(metadata) if metadata else None

        if index_entry:
            index_entry.title = title
            index_entry.content = content
            index_entry.meta_data = meta_str
            index_entry.updated_at = datetime.utcnow()
            await self.search_repo.update(index_entry)
            logger.info(f"Updated index entry for '{entity_type}:{entity_id}'")
        else:
            index_entry = SearchIndex(
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                content=content,
                meta_data=meta_str,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await self.search_repo.create(index_entry)
            logger.info(f"Created new index entry for '{entity_type}:{entity_id}'")

        return index_entry

    async def search(
        self,
        query_str: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Queries the search index with support for filtering, offset pagination, and sorting.
        """
        if not query_str:
            return []

        query = select(SearchIndex).where(SearchIndex.content.ilike(f"%{query_str}%"))
        
        if entity_type:
            query = query.where(SearchIndex.entity_type == entity_type)

        query = query.order_by(SearchIndex.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        
        results = []
        for entry in result.scalars().all():
            results.append({
                "index_id": entry.index_id,
                "entity_type": entry.entity_type,
                "entity_id": entry.entity_id,
                "title": entry.title,
                "content": entry.content,
                "meta_data": entry.meta_data if entry.meta_data else None,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else ""
            })
        return results

    async def rebuild_index(self) -> int:
        """
        Background administrator utility that rebuilds index records for core entities.
        """
        count = 0
        
        # 1. Index Users
        users_result = await self.db.execute(select(User))
        for u in users_result.scalars().all():
            await self.index_entity(
                entity_type="User",
                entity_id=str(u.user_id),
                title=f"{u.first_name or ''} {u.last_name or ''}".strip() or u.email,
                content=f"{u.first_name} {u.last_name} {u.email} {u.employee_code}",
                metadata={"email": u.email, "code": u.employee_code}
            )
            count += 1

        # 2. Index Purchase Requisitions
        pr_result = await self.db.execute(select(PurchaseRequisition))
        for pr in pr_result.scalars().all():
            await self.index_entity(
                entity_type="PurchaseRequisition",
                entity_id=str(pr.pr_id),
                title=f"PR: {pr.pr_number} - {pr.title or ''}",
                content=f"{pr.pr_number} {pr.title} {pr.description or ''} {pr.status} {pr.justification}",
                metadata={"status": pr.status, "pr_number": pr.pr_number}
            )
            count += 1

        # 3. Index Purchase Orders
        po_result = await self.db.execute(select(PurchaseOrder))
        for po in po_result.scalars().all():
            await self.index_entity(
                entity_type="PurchaseOrder",
                entity_id=str(po.po_id),
                title=f"PO: {po.po_number}",
                content=f"{po.po_number} {po.status} {po.delivery_terms or ''}",
                metadata={"status": po.status, "po_number": po.po_number}
            )
            count += 1

        # 4. Index Vendors
        vendor_result = await self.db.execute(select(Vendor))
        for v in vendor_result.scalars().all():
            await self.index_entity(
                entity_type="Vendor",
                entity_id=str(v.vendor_id),
                title=f"Vendor: {v.name}",
                content=f"{v.name} {v.code} {v.email} {v.status}",
                metadata={"code": v.code, "email": v.email}
            )
            count += 1

        logger.info(f"Search index rebuild completed. Indexed {count} total records.")
        return count
