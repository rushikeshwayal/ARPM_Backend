from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey,JSON
from sqlalchemy.sql import func
from database import Base

class ProposalReview(Base):

    __tablename__ = "proposal_reviews"

    id = Column(Integer, primary_key=True)

    proposal_id = Column(Integer, ForeignKey("proposals.id"))

    reviewer_id = Column(Integer, ForeignKey("users.id"))

    role = Column(String)  # "project_manager" | "reviewer" | "committee"

    structured_feedback = Column(JSON)  
    # answers to predefined questions
    general_remark = Column(Text)
    decision = Column(String)  
    created_at = Column(DateTime, server_default=func.now())