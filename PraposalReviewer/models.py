from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class ProposalReviewer(Base):
    __tablename__ = "proposal_reviewers"

    id = Column(Integer, primary_key=True)

    proposal_id = Column(Integer, ForeignKey("proposals.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))

    assigned_by = Column(Integer, ForeignKey("users.id"))  # PM
    assigned_at = Column(DateTime, server_default=func.now())

    status = Column(String, default="pending")  # pending | completed