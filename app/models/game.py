from typing import Optional, Dict, List
from pydantic import BaseModel
from app.models.pagination_links import PaginationLinks

class Game(BaseModel):
    gameId: str
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    genre: Optional[str] = None
    links: Optional[Dict[str, Dict[str, str]]]

class Games(BaseModel):
    games: List[Game]
    links: PaginationLinks