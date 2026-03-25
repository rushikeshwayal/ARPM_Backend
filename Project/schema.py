from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


# ==============================
# CREATE
# ==============================
class ProjectCreate(BaseModel):
    proposal_id: int
    project_manager_id: int

    title: str
    description: Optional[str]

    project_details: Dict[str, Any]   # 🔥 flexible JSON


# ==============================
# RESPONSE
# ==============================


class ProjectResponse(BaseModel):
    id: int
    proposal_id: int
    project_manager_id: int
    title: str
    description: Optional[str] = None      # ✅ must be Optional
    project_details: Optional[Dict[str, Any]] = {}  # ✅ must be Optional
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None  # ✅ must be Optional

    class Config:
        from_attributes = True