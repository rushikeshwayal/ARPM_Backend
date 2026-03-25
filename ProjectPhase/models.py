from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, Boolean, JSON
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


# ─────────────────────────────────────────────────────────────────────────────
# ProjectPhase
# Predefined phases for every project. Created automatically when first
# tranche is released. PM activates them one at a time.
# ─────────────────────────────────────────────────────────────────────────────
class ProjectPhase(Base):

    __tablename__ = "project_phases"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    # Phase identity
    phase_number = Column(Integer, nullable=False)   # 1, 2, 3 ...
    phase_name   = Column(String,  nullable=False)   # "Problem & Literature"
    description  = Column(Text)

    # Status: not_started | active | submitted | revision_requested | completed
    status = Column(String, default="not_started")

    # Who
    activated_by  = Column(Integer, ForeignKey("users.id"))   # PM
    submitted_by  = Column(Integer, ForeignKey("users.id"))   # Lead Researcher
    reviewed_by   = Column(Integer, ForeignKey("users.id"))   # PM

    # Review
    pm_remarks       = Column(Text)
    revision_count   = Column(Integer, default=0)
    iteration  = Column(Integer, default=1)
    is_custom  = Column(Boolean, default=False)

    # Timestamps
    activated_at  = Column(DateTime(timezone=True))
    submitted_at  = Column(DateTime(timezone=True))
    completed_at  = Column(DateTime(timezone=True))
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project")
    steps   = relationship(
        "PhaseStep",
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="PhaseStep.step_number"
    )


# ─────────────────────────────────────────────────────────────────────────────
# PhaseStep
# Each phase has sequential steps. Steps are locked — must complete in order.
# ─────────────────────────────────────────────────────────────────────────────
class PhaseStep(Base):

    __tablename__ = "phase_steps"

    id       = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey("project_phases.id"), nullable=False, index=True)

    # Step identity
    step_number = Column(Integer, nullable=False)   # 1, 2, 3 ...
    step_name   = Column(String,  nullable=False)   # "Define Problem"
    description = Column(Text)

    # Status: not_started | draft | in_progress | submitted | reviewed
    status = Column(String, default="not_started")

    # Content — flexible JSON to hold step-specific data
    # e.g. { "problem_statement": "...", "scope": "..." }
    content = Column(JSON)

    # Researcher notes (plain text fallback)
    notes = Column(Text)

    # Who
    assigned_to  = Column(Integer, ForeignKey("users.id"))   # Lead Researcher
    submitted_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    started_at   = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))
    reviewed_at  = Column(DateTime(timezone=True))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    phase     = relationship("ProjectPhase", back_populates="steps")
    documents = relationship(
        "PhaseStepDocument",
        back_populates="step",
        cascade="all, delete-orphan"
    )


# ─────────────────────────────────────────────────────────────────────────────
# PhaseStepDocument
# Each step can have multiple documents uploaded to Google Drive.
# Document types are predefined per step.
# ─────────────────────────────────────────────────────────────────────────────
class PhaseStepDocument(Base):

    __tablename__ = "phase_step_documents"

    id      = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("phase_steps.id"), nullable=False, index=True)

    document_title = Column(String, nullable=False)
    document_type  = Column(String, nullable=False)   # see STEP_DOCUMENT_TYPES below
    file_path      = Column(String, nullable=False)   # Google Drive URL
    uploaded_by    = Column(Integer, ForeignKey("users.id"))

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    step = relationship("PhaseStep", back_populates="documents")