from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from proposals.models import Proposal, ProposalDocument, ProposalStatus
from proposals.schema import ProposalCreate, ProposalResponse, ProposalDocumentResponse ,ProposalUpdate , SubmitToPMRequest
from services.google_drive import upload_file_to_drive
from PraposalReviewer.models import ProposalReviewer
from datetime import datetime

router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.post("/", response_model=ProposalResponse)
async def create_proposal(
    proposal: ProposalCreate,
    db: AsyncSession = Depends(get_db)
):

    db_proposal = Proposal(**proposal.model_dump())

    db.add(db_proposal)

    await db.commit()

    await db.refresh(db_proposal)

    return db_proposal


@router.get("/", response_model=list[ProposalResponse]) 
async def get_proposals(db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Proposal))

    proposals = result.scalars().all()

    return proposals


@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(proposal_id: int, db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(Proposal).where(Proposal.id == proposal_id)
    )

    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return proposal


@router.post("/upload-document")
async def upload_document(
    proposal_id: int = Form(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    uploaded_by: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):

    file_bytes = await file.read()

    drive_url = upload_file_to_drive(file_bytes, file.filename)

    db_document = ProposalDocument(
        proposal_id=proposal_id,
        document_name=document_name,
        document_type=document_type,
        file_path=drive_url,
        uploaded_by=uploaded_by
    )

    db.add(db_document)

    await db.commit()

    await db.refresh(db_document)

    return db_document

@router.get("/{proposal_id}/documents", response_model=list[ProposalDocumentResponse])
async def get_documents_by_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(ProposalDocument).where(
            ProposalDocument.proposal_id == proposal_id
        )
    )

    documents = result.scalars().all()

    return documents

@router.put("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: int,
    proposal_update: ProposalUpdate,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(Proposal).where(Proposal.id == proposal_id)
    )

    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Allow editing only in specific statuses
    allowed_statuses = [
        ProposalStatus.draft,
        ProposalStatus.returned_by_pm,
        ProposalStatus.returned_by_reviewer
    ]

    if proposal.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Proposal cannot be edited in current status"
        )

    update_data = proposal_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(proposal, field, value)

    # If proposal was returned and researcher edits it,
    # bring it back to draft state
    if proposal.status in [
        ProposalStatus.returned_by_pm,
        ProposalStatus.returned_by_reviewer
    ]:
        proposal.status = ProposalStatus.draft

    await db.commit()
    await db.refresh(proposal)

    return proposal


@router.post("/{proposal_id}/submit")
async def submit_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):
    proposal = await db.get(Proposal, proposal_id)

    if not proposal:
        raise HTTPException(404, "Proposal not found")

    # ✅ Only allow submit from draft OR returned_to_draft
    if proposal.status not in ["draft", "returned_to_draft"]:
        raise HTTPException(400, "Only draft proposals can be submitted")

    # ✅ Move to PM stage
    proposal.status = "submitted_to_pm"

    await db.commit()

    return {"message": "Proposal submitted to Project Manager"}
@router.put("/documents/{document_id}/replace")
async def replace_document_file(
    document_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(ProposalDocument).where(ProposalDocument.id == document_id)
    )

    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    proposal = await db.get(Proposal, document.proposal_id)

    allowed_status = [
        ProposalStatus.draft,
        ProposalStatus.returned_by_pm,
        ProposalStatus.returned_by_reviewer
    ]

    if proposal.status not in allowed_status:
        raise HTTPException(
            status_code=400,
            detail="Cannot replace document after submission"
        )

    file_bytes = await file.read()

    drive_url = upload_file_to_drive(file_bytes, file.filename)

    document.file_path = drive_url

    await db.commit()

    return {"message": "Document replaced successfully"}

@router.get("/pm/{pm_id}", response_model=list[ProposalResponse])
async def get_proposals_by_pm(
    pm_id: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(Proposal).where(
            Proposal.assigned_pm_id == pm_id,
            Proposal.status != ProposalStatus.draft   # ✅ exclude draft
        )
    )

    proposals = result.scalars().all()

    return proposals

@router.get("/reviewer/{reviewer_id}", response_model=list[ProposalResponse])
async def get_proposals_by_reviewer(
    reviewer_id: int,
    db: AsyncSession = Depends(get_db)
):

    # ✅ Step 1: Check user exists (optional but good)
    # (skip for now if you want lightweight)

    # ✅ Step 2: Get all assigned proposal_ids
    result = await db.execute(
        select(ProposalReviewer.proposal_id).where(
            ProposalReviewer.reviewer_id == reviewer_id
        )
    )

    proposal_ids = [row[0] for row in result.all()]

    if not proposal_ids:
        return []

    # ✅ Step 3: Fetch all proposals in ONE query
    result = await db.execute(
        select(Proposal).where(
            Proposal.id.in_(proposal_ids)
        )
    )

    proposals = result.scalars().all()

    return proposals