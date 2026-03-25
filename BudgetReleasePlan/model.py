from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, Numeric, Boolean
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Budget Release Plan  (master)
# ─────────────────────────────────────────────────────────────────────────────
class BudgetReleasePlan(Base):

    __tablename__ = "budget_release_plans"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    # Core
    total_sanctioned_amount = Column(Numeric(15, 2), nullable=False)
    currency                = Column(String, default="INR")
    plan_version            = Column(Integer, default=1)   # v1, v2 …

    # Status: draft | active | locked | revised | archived
    status = Column(String, default="draft")

    # Who
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project  = relationship("Project")
    tranches = relationship(
        "BudgetTranche",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="BudgetTranche.id"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Budget Tranche  (child)
# ─────────────────────────────────────────────────────────────────────────────
class BudgetTranche(Base):

    __tablename__ = "budget_tranches"

    id      = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("budget_release_plans.id"), nullable=False, index=True)

    # Identity
    tranche_name = Column(String, nullable=False)   # e.g. "Initial Release"
    description  = Column(Text)
    amount       = Column(Numeric(15, 2), nullable=False)

    # Release type: manual | milestone_based | time_based
    release_type = Column(String, nullable=False, default="manual")

    # ── Release Condition ─────────────────────────────────────────────────────
    # condition_type : manual | phase_start | phase_completion | date
    condition_type  = Column(String, default="manual")
    condition_value = Column(String)          # phase_id OR date string OR event
    has_dependency  = Column(Boolean, default=False)

    # ── Documents ─────────────────────────────────────────────────────────────
    tranche_justification_doc_url = Column(String)   # why this tranche exists
    release_approval_doc_url      = Column(String)   # proof of release auth

    # ── Status Tracking ───────────────────────────────────────────────────────
    # pending | approved | released | blocked
    status = Column(String, default="pending")

    released_amount        = Column(Numeric(15, 2), default=0)
    release_date           = Column(DateTime(timezone=True))
    released_by            = Column(Integer, ForeignKey("users.id"))
    transaction_reference  = Column(String)
    remarks                = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plan = relationship("BudgetReleasePlan", back_populates="tranches")