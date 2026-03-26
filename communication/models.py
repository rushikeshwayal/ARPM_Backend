from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)

    attachment = Column(String, nullable=True)  # file path or URL

    created_at = Column(DateTime(timezone=True), server_default=func.now())