from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.cns import (
    CNSSearchResponse,
    CNSDatabaseListResponse,
    CNSBatchCheckRequest,
    CNSBatchCheckResponse
)
from app.services import cns_service
from typing import Optional

router = APIRouter(prefix="/cns", tags=["cns"])


@router.get("/search", response_model=CNSSearchResponse)
def search_sanctions_database(
    name: str = Query(..., description="Name to search"),
    type: Optional[str] = Query("BOTH", description="Search type (INDIVIDUAL/ENTITY/BOTH)"),
    country: Optional[str] = Query(None, description="Country code filter (ISO 3166-1 alpha-2)"),
    fuzzy: bool = Query(True, description="Enable fuzzy matching"),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum match confidence"),
    db: Session = Depends(get_db)
):
    """
    Search CNS (Central Name Search) sanctions and watchlist databases
    
    - **name**: Name to search for (required)
    - **type**: Search for INDIVIDUAL, ENTITY, or BOTH
    - **country**: Filter by country code (e.g., 'USA', 'GBR')
    - **fuzzy**: Enable fuzzy/similarity matching
    - **min_confidence**: Minimum confidence score (0.0-1.0)
    
    Returns matches from OFAC SDN, UN Sanctions, EU Sanctions databases
    """
    return cns_service.search_cns(db, name, type, country, fuzzy, min_confidence)


@router.get("/databases", response_model=CNSDatabaseListResponse)
def list_cns_databases(db: Session = Depends(get_db)):
    """
    List available CNS databases with metadata
    
    Returns:
    - Database ID, name, description
    - Last updated timestamp
    - Record count
    - Enabled status
    """
    return cns_service.get_databases(db)


@router.post("/batch-check", response_model=CNSBatchCheckResponse)
def batch_check_users(
    request: CNSBatchCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Batch check multiple users against CNS databases
    
    - **user_ids**: List of user IDs to check
    
    Returns:
    - Total users checked
    - Number of matches found
    - Individual results for each user with match confidence
    """
    if not request.user_ids:
        raise HTTPException(status_code=400, detail="user_ids list cannot be empty")
    
    if len(request.user_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 users per batch")
    
    return cns_service.batch_check_users(db, request.user_ids)
