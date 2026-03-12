from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CNSDatabaseInfo(BaseModel):
    id: str
    name: str
    full_name: str
    description: Optional[str]
    country: str
    last_updated: datetime
    record_count: int
    enabled: bool

    class Config:
        from_attributes = True


class CNSDatabaseListResponse(BaseModel):
    databases: List[CNSDatabaseInfo]


class CNSMatchResult(BaseModel):
    match_id: str
    name: str
    confidence: float
    source: str
    database_id: str
    list_type: str
    entity_type: str
    country: Optional[str]
    date_of_birth: Optional[str]
    aka_names: Optional[List[str]]
    added_date: str
    program: str
    remarks: Optional[str]
    risk_level: str

    class Config:
        from_attributes = True


class CNSSearchResponse(BaseModel):
    query: str
    total_matches: int
    search_time_ms: int
    databases_searched: List[str]
    matches: List[CNSMatchResult]


class CNSBatchCheckRequest(BaseModel):
    user_ids: List[int]


class CNSBatchCheckResult(BaseModel):
    user_id: int
    user_name: str
    match_found: bool
    match_count: Optional[int] = 0
    highest_confidence: Optional[float] = None
    risk_level: Optional[str] = None


class CNSBatchCheckResponse(BaseModel):
    total_checked: int
    matches_found: int
    results: List[CNSBatchCheckResult]
