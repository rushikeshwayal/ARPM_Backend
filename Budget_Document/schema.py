from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BudgetDocumentResponse(BaseModel):
    id:             int
    budget_id:      int
    document_title: str
    document_type:  str
    file_path:      str
    uploaded_by:    Optional[int]
    uploaded_at:    datetime

    class Config:
        from_attributes = True