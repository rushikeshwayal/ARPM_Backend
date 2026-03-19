from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProposalReviewerCreate(BaseModel):
    proposal_id: int
    reviewer_id: int
    assigned_by: int
    status: Optional[str] = "pending"


class ProposalReviewerResponse(BaseModel):
    id: int
    proposal_id: int
    reviewer_id: int
    assigned_by: int
    assigned_at: datetime
    status: str

    class Config:
        from_attributes = True