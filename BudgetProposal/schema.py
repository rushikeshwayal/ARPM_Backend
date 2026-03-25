from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


# ── Create ────────────────────────────────────────────────────────────────────
class BudgetProposalCreate(BaseModel):

    project_id:   int
    created_by:   int

    total_budget:  int
    justification: Optional[str] = None

    compute_cost:          Optional[int] = 0
    data_acquisition_cost: Optional[int] = 0
    manpower_cost:         Optional[int] = 0
    infrastructure_cost:   Optional[int] = 0
    miscellaneous_cost:    Optional[int] = 0

    budget_breakdown: Optional[Dict] = None


# ── Submit (PM sends to committee) ───────────────────────────────────────────
class BudgetSubmit(BaseModel):
    submitted_by: int   # must match project_manager_id


# ── Committee Action ─────────────────────────────────────────────────────────
class BudgetReview(BaseModel):
    reviewed_by:       int
    action:            str   # "approved" | "revision_requested"
    committee_remarks: Optional[str] = None


# ── Response ─────────────────────────────────────────────────────────────────
class BudgetProposalResponse(BaseModel):

    id:         int
    project_id: int
    created_by: int

    total_budget:  int
    justification: Optional[str]

    compute_cost:          Optional[int]
    data_acquisition_cost: Optional[int]
    manpower_cost:         Optional[int]
    infrastructure_cost:   Optional[int]
    miscellaneous_cost:    Optional[int]

    budget_breakdown: Optional[dict]

    status:            str
    committee_remarks: Optional[str]
    revision_count:    int

    created_at:   datetime
    updated_at:   Optional[datetime]
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True