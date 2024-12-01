from typing import Optional, Dict
from pydantic import BaseModel

class PaginationLinks(BaseModel):
    self: Dict[str, str]
    next: Optional[Dict[str, str]]
    prev: Optional[Dict[str, str]]