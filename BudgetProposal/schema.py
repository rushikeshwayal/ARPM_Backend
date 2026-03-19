from pydantic import BaseModel
from typing import Optional, Dict


class BudgetProposalCreate(BaseModel):

    proposal_id: int
    created_by: int

    total_budget: int
    justification: Optional[str]

    compute_cost: Optional[int]
    data_acquisition_cost: Optional[int]
    manpower_cost: Optional[int]
    infrastructure_cost: Optional[int]
    miscellaneous_cost: Optional[int]

    budget_breakdown: Optional[Dict]


class BudgetProposalResponse(BaseModel):

    id: int
    proposal_id: int
    created_by: int

    total_budget: int
    justification: Optional[str]

    compute_cost: Optional[int]
    data_acquisition_cost: Optional[int]
    manpower_cost: Optional[int]
    infrastructure_cost: Optional[int]
    miscellaneous_cost: Optional[int]

    budget_breakdown: Optional[dict]

    status: str

    class Config:
        from_attributes = True