from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from database import get_db
from communication.models import Message
from communication.schema import MessageResponse

from database import get_db
from communication.models import Message
from communication.schema import MessageCreate, MessageResponse

router = APIRouter(prefix="/messages", tags=["Messages"])

from services.google_drive import upload_file_to_drive   # adjust path if needed

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("/send", response_model=List[MessageResponse])
async def send_message(
    sender_id: int = Form(...),
    receiver_ids: List[int] = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    attachment_url = None

    if file:
        file_bytes = await file.read()
        attachment_url = upload_file_to_drive(file_bytes, file.filename)

    created_messages = []

    for receiver_id in receiver_ids:
        msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            subject=subject,
            body=body,
            attachment=attachment_url
        )
        db.add(msg)
        created_messages.append(msg)

    await db.commit()

    for msg in created_messages:
        await db.refresh(msg)

    return created_messages


# 📥 GET INBOX (messages received)
@router.get("/inbox/{user_id}", response_model=List[MessageResponse])
async def get_inbox(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.receiver_id == user_id)
    )
    messages = result.scalars().all()
    return messages


# 📤 GET SENT MESSAGES
@router.get("/sent/{user_id}", response_model=List[MessageResponse])
async def get_sent(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.sender_id == user_id)
    )
    messages = result.scalars().all()
    return messages