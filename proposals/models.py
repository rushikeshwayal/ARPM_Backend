from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from database import Base

class ProposalStatus(str, enum.Enum):

    draft = "draft"

    submitted_to_pm = "submitted_to_pm"

    returned_to_draft = "returned_to_draft"   # NEW (important)

    submitted_to_reviewers = "submitted_to_reviewers"

    review_completed = "review_completed"

    submitted_to_committee = "submitted_to_committee"

    approved = "approved"
    rejected = "rejected" 


class Proposal(Base):

    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    lead_researcher_id = Column(
        Integer,
        ForeignKey("users.id"),
        index=True
    )

    research_domain = Column(String)

    abstract = Column(Text)
    problem_statement = Column(Text)
    motivation = Column(Text)
    objectives = Column(Text)
    methodology_overview = Column(Text)
    novelty = Column(Text)
    expected_outcomes = Column(Text)
    potential_impact = Column(Text)

    proposed_duration_months = Column(Integer)
    rough_budget_estimate = Column(Integer)
    team_size_estimate = Column(Integer)
    required_resources_summary = Column(Text)
    assigned_pm_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(ProposalStatus), default=ProposalStatus.draft)

    submitted_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    documents = relationship(
        "ProposalDocument",
        back_populates="proposal",
        cascade="all, delete"
    )


class ProposalDocument(Base):

    __tablename__ = "proposal_documents"

    id = Column(Integer, primary_key=True, index=True)

    proposal_id = Column(
        Integer,
        ForeignKey("proposals.id"),
        index=True
    )

    document_name = Column(String)
    document_type = Column(String)

    file_path = Column(String)

    uploaded_by = Column(
        Integer,
        ForeignKey("users.id")
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    proposal = relationship("Proposal", back_populates="documents")