from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ─────────────────────────────────────────────────────────────────────────────
# Tranche Schemas
# ─────────────────────────────────────────────────────────────────────────────

class TrancheCreate(BaseModel):
    tranche_name:  str
    description:   Optional[str]  = None
    amount:        Decimal

    release_type:   str = "manual"   # manual | milestone_based | time_based
    condition_type: str = "manual"   # manual | phase_start | phase_completion | date
    condition_value: Optional[str]   = None
    has_dependency:  bool            = False

    tranche_justification_doc_url: Optional[str] = None
    release_approval_doc_url:      Optional[str] = None


class TrancheUpdate(BaseModel):
    tranche_name:   Optional[str]     = None
    description:    Optional[str]     = None
    amount:         Optional[Decimal] = None
    release_type:   Optional[str]     = None
    condition_type: Optional[str]     = None
    condition_value: Optional[str]    = None
    has_dependency:  Optional[bool]   = None
    tranche_justification_doc_url: Optional[str] = None
    release_approval_doc_url:      Optional[str] = None


class TrancheRelease(BaseModel):
    released_by:           int
    released_amount:       Decimal
    transaction_reference: Optional[str] = None
    remarks:               Optional[str] = None


class TrancheResponse(BaseModel):
    id:           int
    plan_id:      int
    tranche_name: str
    description:  Optional[str]
    amount:       Decimal

    release_type:    str
    condition_type:  str
    condition_value: Optional[str]
    has_dependency:  bool

    tranche_justification_doc_url: Optional[str]
    release_approval_doc_url:      Optional[str]

    status:                str
    released_amount:       Optional[Decimal]
    release_date:          Optional[datetime]
    released_by:           Optional[int]
    transaction_reference: Optional[str]
    remarks:               Optional[str]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Release Plan Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ReleasePlanCreate(BaseModel):
    project_id:              int
    created_by:              int
    total_sanctioned_amount: Decimal
    currency:                str              = "INR"
    notes:                   Optional[str]    = None


class ReleasePlanResponse(BaseModel):
    id:                      int
    project_id:              int
    total_sanctioned_amount: Decimal
    currency:                str
    plan_version:            int
    status:                  str
    created_by:              int
    approved_by:             Optional[int]
    notes:                   Optional[str]
    created_at:              datetime
    updated_at:              Optional[datetime]
    tranches:                List[TrancheResponse] = []

    # Computed summaries (populated by router)
    total_allocated: Optional[Decimal] = None
    total_released:  Optional[Decimal] = None
    remaining:       Optional[Decimal] = None

    class Config:
        from_attributes = True