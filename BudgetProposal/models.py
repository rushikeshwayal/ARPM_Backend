from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class BudgetProposal(Base):
 
    __tablename__ = "budget_proposals"
 
    id = Column(Integer, primary_key=True, index=True)
 
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        unique=True,
        nullable=False,
        index=True
    )
 
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
 
    total_budget  = Column(Integer, nullable=False)
    justification = Column(Text)
 
    compute_cost          = Column(Integer, default=0)
    data_acquisition_cost = Column(Integer, default=0)
    manpower_cost         = Column(Integer, default=0)
    infrastructure_cost   = Column(Integer, default=0)
    miscellaneous_cost    = Column(Integer, default=0)
 
    budget_breakdown = Column(JSON)
 
    status = Column(String, default="draft")
 
    committee_remarks = Column(Text)
    revision_count    = Column(Integer, default=0)
 
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True))
 
    # ── Relationships ──────────────────────────────────────────────────────────
    project  = relationship("Project")
    creator  = relationship("User", foreign_keys=[created_by])
 
    # ✅ THIS WAS MISSING — BudgetDocument.back_populates="budget" points here
    documents = relationship(
        "BudgetDocument",
        back_populates="budget",
        cascade="all, delete-orphan"
    )
 