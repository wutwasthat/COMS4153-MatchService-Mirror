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
    isActive: bool = False
    isCancelled: bool = False

class MatchRequestWithLinks(MatchRequest):
    links: Dict[str, Dict[str, str]]

class MatchRequestResponse(BaseModel):
    matchRequests: List[MatchRequestWithLinks]
    links: PaginationLinks

class MatchRequestInitiate(BaseModel):
    MatchRequestId: str

class MatchmakingStatus(BaseModel):
    matchRequestId: str
    status: str  # Possible values: "matching", "matched", "not_found", "error"
    partnerRequestId: Optional[str]

class FavGameRequest(BaseModel):
    user_id: str
    game_id: str
    match_request_id: str = None

    def to_db(self):
        return {
            "userId": self.user_id, 
            "gameId": self.game_id,
            "matchRequestId": self.match_request_id
        }