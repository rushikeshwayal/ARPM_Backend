from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from database import Base


class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    proposal_id = Column(
        Integer,
        ForeignKey("proposals.id"),
        unique=True,
        nullable=False
    )

    project_manager_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(String, nullable=False)
    description = Column(Text)

    project_details = Column(JSON, nullable=False)

    # ✅ Plain String — bypasses the broken projectstatus enum entirely
    status = Column(String, nullable=False, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )