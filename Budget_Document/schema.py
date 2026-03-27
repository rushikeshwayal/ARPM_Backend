from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class BudgetDocumentResponse(BaseModel):
    id:             int
    budget_id:      int
    document_title: str
    document_type:  str
    file_path:      str
    uploaded_by:    Optional[int]
    uploaded_at:    datetime

    doc_summary: Optional[Dict[str, Any]]  # ✅ NEW

    class Config:
        from_attributes = True