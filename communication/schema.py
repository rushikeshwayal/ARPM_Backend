from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# 📩 SEND MESSAGE (Request Schema)
class MessageCreate(BaseModel):
    receiver_id: int
    subject: str
    body: str
    attachment: Optional[str] = None


# 📥 RESPONSE SCHEMA (Common for Inbox & Sent)
class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    subject: str
    body: str
    attachment: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True