from typing import Optional, Dict, List
from pydantic import BaseModel
from app.models.pagination_links import PaginationLinks
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Text

Base = declarative_base()


class GameInfo(Base):
    __tablename__ = 'game_info'
    __table_args__ = {'schema': 'Game'}

    gameId = Column(String(36), primary_key=True)
    image = Column(String(255))
    title = Column(String(255))
    description = Column(Text)
    genre = Column(Text)

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