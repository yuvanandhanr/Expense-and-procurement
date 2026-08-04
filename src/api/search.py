from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.schemas.platform_services import SearchResult
from src.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=List[SearchResult])
async def search(
    q: str = Query(..., description="Query string for search"),
    entity_type: Optional[str] = Query(None, description="Optional entity type filter (e.g. PR, PO, Vendor)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Search globally across all system entities.
    """
    service = SearchService(db)
    results = await service.search(query_str=q, entity_type=entity_type, limit=limit, offset=offset)
    return results


@router.post("/rebuild")
async def rebuild_index(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Rebuild the full text search index from current DB records.
    """
    service = SearchService(db)
    indexed_count = await service.rebuild_index()
    return {"status": "success", "message": f"Successfully indexed {indexed_count} entities"}
