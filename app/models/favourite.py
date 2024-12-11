from pydantic import BaseModel, Field
import uuid
from typing import List
from app.models.game import Game

class Favourite(BaseModel):
    favouriteId : str = Field(default_factory=lambda: str(uuid.uuid4()))  # Automatically generate UUID
    userId: str
    gameId: str

class Favourites(BaseModel):
    games: List[Game]