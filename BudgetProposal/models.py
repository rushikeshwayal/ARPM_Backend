from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class BudgetProposal(Base):

    __tablename__ = "budget_proposals"

    id = Column(Integer, primary_key=True, index=True)

    proposal_id = Column(Integer, ForeignKey("proposals.id"), index=True)

    created_by = Column(Integer, ForeignKey("users.id"))

    # 🔥 HIGH LEVEL
    total_budget = Column(Integer)
    justification = Column(Text)

    # 🔥 AI R&D SPECIFIC (VERY IMPORTANT)
    compute_cost = Column(Integer)
    data_acquisition_cost = Column(Integer)
    manpower_cost = Column(Integer)
    infrastructure_cost = Column(Integer)
    miscellaneous_cost = Column(Integer)

    # 🔥 STRUCTURED BREAKDOWN (FLEXIBLE)
    budget_breakdown = Column(JSON)

    status = Column(String, default="draft")  # draft / submitted / approved / rejected

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    proposal = relationship("Proposal")