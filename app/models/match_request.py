from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import uuid
from app.models.pagination_links import PaginationLinks

class MatchRequest(BaseModel):
    userId: str
    gameId: str
    matchRequestId: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Automatically generate UUID
    expireDate: str  # Use str for date or adjust to use a specific date type
    isActive: bool = False
    isCancelled: bool = False

class MatchRequestWithLinks(MatchRequest):
    links: Dict[str, Dict[str, str]]

class MatchRequests(BaseModel):
    matchRequests: List[MatchRequestWithLinks]
    links: PaginationLinks