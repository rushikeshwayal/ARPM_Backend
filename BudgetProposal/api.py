from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from database import get_db
from proposals.models import Proposal, ProposalStatus, ProposalDocument
from BudgetProposal.models import BudgetProposal
from services.google_drive import upload_file_to_drive

router = APIRouter(prefix="/budget-proposals", tags=["Budget Proposals"])

@router.post("/{proposal_id}/budget")
async def create_budget_with_documents(
    proposal_id: int,

    created_by: int = Form(...),

    total_budget: int = Form(...),
    justification: str = Form(None),

    compute_cost: int = Form(0),
    data_acquisition_cost: int = Form(0),
    manpower_cost: int = Form(0),
    infrastructure_cost: int = Form(0),
    miscellaneous_cost: int = Form(0),

    budget_breakdown: str = Form(None),

    document_meta: str = Form(None),

    files: list[UploadFile] = File([]),

    db: AsyncSession = Depends(get_db)
):

    # 🔥 Validate proposal
    proposal = await db.get(Proposal, proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != ProposalStatus.approved:
        raise HTTPException(
            status_code=400,
            detail="Budget allowed only after proposal approval"
        )

    # 🔥 Parse breakdown JSON
    breakdown_json = None
    if budget_breakdown:
        try:
            breakdown_json = json.loads(budget_breakdown)
        except:
            raise HTTPException(status_code=400, detail="Invalid breakdown JSON")

    # 🔥 Parse document metadata
    doc_meta_list = []
    if document_meta:
        try:
            doc_meta_list = json.loads(document_meta)
        except:
            raise HTTPException(status_code=400, detail="Invalid document metadata JSON")

    # 🔥 Create budget
    budget = BudgetProposal(
        proposal_id=proposal_id,
        created_by=created_by,

        total_budget=total_budget,
        justification=justification,

        compute_cost=compute_cost,
        data_acquisition_cost=data_acquisition_cost,
        manpower_cost=manpower_cost,
        infrastructure_cost=infrastructure_cost,
        miscellaneous_cost=miscellaneous_cost,

        budget_breakdown=breakdown_json
    )

    db.add(budget)
    await db.flush()

    # 🔥 Upload documents
    uploaded_docs = []

    for idx, file in enumerate(files):

        meta = doc_meta_list[idx] if idx < len(doc_meta_list) else {}

        file_bytes = await file.read()
        drive_url = upload_file_to_drive(file_bytes, file.filename)

        doc = ProposalDocument(
            proposal_id=proposal_id,
            document_name=meta.get("name", file.filename),
            document_type=meta.get("type", "budget"),
            file_path=drive_url,
            uploaded_by=created_by
        )

        db.add(doc)
        uploaded_docs.append(doc)

    await db.commit()

    return {
        "message": "Budget created successfully",
        "budget_id": budget.id,
        "documents_uploaded": len(uploaded_docs)
    }

@router.get("/{proposal_id}")
async def get_budget_by_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):

    # 🔥 Get budget
    result = await db.execute(
        select(BudgetProposal).where(
            BudgetProposal.proposal_id == proposal_id
        )
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # 🔥 Get documents
    result = await db.execute(
        select(ProposalDocument).where(
            ProposalDocument.proposal_id == proposal_id,
            ProposalDocument.document_type != None
        )
    )
    documents = result.scalars().all()

    return {
        "budget": {
            "id": budget.id,
            "proposal_id": budget.proposal_id,
            "created_by": budget.created_by,
            "total_budget": budget.total_budget,
            "justification": budget.justification,

            "compute_cost": budget.compute_cost,
            "data_acquisition_cost": budget.data_acquisition_cost,
            "manpower_cost": budget.manpower_cost,
            "infrastructure_cost": budget.infrastructure_cost,
            "miscellaneous_cost": budget.miscellaneous_cost,

            "budget_breakdown": budget.budget_breakdown,
            "status": budget.status
        },

        "documents": [
            {
                "id": doc.id,
                "name": doc.document_name,
                "type": doc.document_type,
                "file": doc.file_path
            }
            for doc in documents
        ]
    }