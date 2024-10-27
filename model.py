from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import uuid
from datetime import date

class Game(BaseModel):
    gameId: str
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    genre: Optional[str] = None

class GameWithLinks(Game):
    links: Dict[str, Dict[str, str]]

class PaginationLinks(BaseModel):
    self: Dict[str, str]
    next: Optional[Dict[str, str]]
    prev: Optional[Dict[str, str]]

class GamesResponse(BaseModel):
    games: List[GameWithLinks]
    links: PaginationLinks

class MatchRequest(BaseModel):
    userId: str
    gameId: str
    matchRequestId: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Automatically generate UUID
    expireDate: str  # Use str for date or adjust to use a specific date type
    isActive: bool = True
    isCancelled: bool = False

class MatchRequestWithLinks(MatchRequest):
    links: Dict[str, Dict[str, str]]

class MatchRequestResponse(BaseModel):
    matchRequests: List[MatchRequestWithLinks]
    links: PaginationLinks