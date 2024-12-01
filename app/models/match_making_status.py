from typing import Optional
from pydantic import BaseModel

class MatchMakingStatus(BaseModel):
    matchRequestId: str
    status: str  # Possible values: "matching", "matched", "not_found", "error"
    partnerRequestId: Optional[str] = None