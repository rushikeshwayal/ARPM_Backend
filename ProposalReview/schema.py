from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ProposalReviewResponse(BaseModel):

    id: int
    proposal_id: int
    reviewer_id: int
    role: str

    structured_feedback: Optional[Dict[str, Any]]
    general_remark: Optional[str]
    decision: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True

class ProposalReviewCreate(BaseModel):

    proposal_id: int
    reviewer_id: int
    role: str   # "project_manager" | "reviewer" | "committee"

    structured_feedback: Optional[Dict[str, Any]] = None
    general_remark: Optional[str] = None
    decision: Optional[str] = None