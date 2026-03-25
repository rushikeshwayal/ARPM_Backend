from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class BudgetDocument(Base):
 
    __tablename__ = "budget_documents"
 
    id = Column(Integer, primary_key=True, index=True)
 
    budget_id = Column(
        Integer,
        ForeignKey("budget_proposals.id"),
        nullable=False,
        index=True
    )
 
    document_title = Column(String, nullable=False)
    document_type  = Column(String, nullable=False)
    file_path      = Column(String, nullable=False)
    uploaded_by    = Column(Integer, ForeignKey("users.id"))
 
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
 
    # ✅ Points back to BudgetProposal.documents
    budget = relationship("BudgetProposal", back_populates="documents")

# ── Add this to BudgetProposal model (budget_model.py) ───────────────────────
# documents = relationship("BudgetDocument", back_populates="budget", cascade="all, delete-orphan")

# ── PREDEFINED DOCUMENT TYPES ─────────────────────────────────────────────────
BUDGET_DOCUMENT_TYPES = [
    "compute_cost_quote",
    "data_acquisition_plan",
    "manpower_breakdown",
    "infrastructure_quote",
    "miscellaneous_justification",
    "other",
]