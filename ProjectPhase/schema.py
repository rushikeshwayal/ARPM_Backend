from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Document ─────────────────────────────────────────────────────────────────
class StepDocumentResponse(BaseModel):
    id:             int
    step_id:        int
    document_title: str
    document_type:  str
    file_path:      str
    uploaded_by:    Optional[int]
    uploaded_at:    datetime

    class Config:
        from_attributes = True


# ─── Step ─────────────────────────────────────────────────────────────────────
class StepContentUpdate(BaseModel):
    content:      Optional[Dict[str, Any]] = None
    notes:        Optional[str]            = None
    assigned_to:  Optional[int]            = None


class StepResponse(BaseModel):
    id:           int
    phase_id:     int
    step_number:  int
    step_name:    str
    description:  Optional[str]
    status:       str
    content:      Optional[Dict[str, Any]]
    notes:        Optional[str]
    assigned_to:  Optional[int]
    submitted_by: Optional[int]
    started_at:   Optional[datetime]
    submitted_at: Optional[datetime]
    reviewed_at:  Optional[datetime]
    created_at:   datetime
    updated_at:   Optional[datetime]
    documents:    List[StepDocumentResponse] = []

    class Config:
        from_attributes = True


# ─── Phase ────────────────────────────────────────────────────────────────────
class PhaseActivate(BaseModel):
    activated_by: int   # must be PM


class PhaseSubmit(BaseModel):
    submitted_by: int   # must be Lead Researcher


class PhaseReview(BaseModel):
    reviewed_by: int
    action:      str          # "approved" | "revision_requested"
    pm_remarks:  Optional[str] = None


class PhaseResponse(BaseModel):
    id:           int
    project_id:   int
    phase_number: int
    phase_name:   str
    description:  Optional[str]
    status:       str

    activated_by:   Optional[int]
    submitted_by:   Optional[int]
    reviewed_by:    Optional[int]
    pm_remarks:     Optional[str]
    revision_count: int

    activated_at:  Optional[datetime]
    submitted_at:  Optional[datetime]
    completed_at:  Optional[datetime]
    created_at:    datetime
    updated_at:    Optional[datetime]

    steps: List[StepResponse] = []

    # Computed
    total_steps:     Optional[int] = None
    completed_steps: Optional[int] = None
    progress_pct:    Optional[int] = None

    class Config:
        from_attributes = True


# ─── Phase visibility check response ─────────────────────────────────────────
class PhaseVisibilityResponse(BaseModel):
    visible:                bool
    reason:                 str
    tranche_released_count: int
    phases:                 List[PhaseResponse] = []

class CustomStepCreate(BaseModel):
    step_number: int
    step_name:   str
    description: Optional[str] = None
 
 
class CustomPhaseCreate(BaseModel):
    phase_name:   str
    description:  Optional[str] = None
    phase_number: int
    iteration:    int  = 1
    is_custom:    bool = True
    created_by:   int
    steps:        List[CustomStepCreate] = []