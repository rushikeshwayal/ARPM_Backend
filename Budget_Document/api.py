from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List
import json

from database import get_db
from BudgetProposal.models import BudgetProposal
from Budget_Document.model import BudgetDocument
from BudgetProposal.schema import (
    BudgetProposalCreate,
    BudgetProposalResponse,
    BudgetSubmit,
    BudgetReview,
)
from Budget_Document.schema import BudgetDocumentResponse
from Project.models import Project
from services.google_drive import upload_file_to_drive

router = APIRouter(prefix="/budget", tags=["Budget"])


# ─────────────────────────────────────────────────────────────────────────────
# 1. CREATE budget draft
# POST /budget/
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/", response_model=BudgetProposalResponse)
async def create_budget(
    payload: BudgetProposalCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    if project.project_manager_id != payload.created_by:
        raise HTTPException(403, "Only the project manager can create a budget")

    existing = await db.execute(
        select(BudgetProposal).where(
            BudgetProposal.project_id == payload.project_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Budget already exists for this project")

    budget = BudgetProposal(**payload.model_dump())
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET budget for a project
# GET /budget/project/{project_id}
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/project/{project_id}", response_model=BudgetProposalResponse)
async def get_budget(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BudgetProposal).where(
            BudgetProposal.project_id == project_id
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(404, "No budget found for this project")
    return budget


# ─────────────────────────────────────────────────────────────────────────────
# 3. UPLOAD multiple documents for a budget
# POST /budget/{budget_id}/documents
#
# Form fields:
#   uploaded_by   : int
#   document_meta : JSON string → [{"title": "...", "type": "..."}, ...]
#   files         : list of files
#
# Example document_meta:
# [
#   {"title": "Compute Cost Quote",       "type": "compute_cost_quote"},
#   {"title": "Manpower Breakdown Sheet", "type": "manpower_breakdown"}
# ]
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{budget_id}/documents")
async def upload_budget_documents(
    budget_id:     int,
    uploaded_by:   int            = Form(...),
    document_meta: str            = Form(...),   # JSON string
    files:         List[UploadFile] = File(...),
    db:            AsyncSession   = Depends(get_db),
):
    # ── Validate budget ──
    budget = await db.get(BudgetProposal, budget_id)
    if not budget:
        raise HTTPException(404, "Budget not found")

    if budget.status not in ("draft", "revision_requested"):
        raise HTTPException(400, "Documents can only be uploaded in draft or revision state")

    # ── Parse metadata ──
    try:
        meta_list = json.loads(document_meta)
    except Exception:
        raise HTTPException(400, "Invalid document_meta JSON")

    if len(files) != len(meta_list):
        raise HTTPException(
            400,
            f"Mismatch: {len(files)} files but {len(meta_list)} metadata entries"
        )

    # ── Upload each file to Drive ──
    uploaded = []
    for file, meta in zip(files, meta_list):
        file_bytes = await file.read()
        drive_url  = upload_file_to_drive(file_bytes, file.filename)

        doc = BudgetDocument(
            budget_id      = budget_id,
            document_title = meta.get("title", file.filename),
            document_type  = meta.get("type", "other"),
            file_path      = drive_url,
            uploaded_by    = uploaded_by,
        )
        db.add(doc)
        uploaded.append(doc)

    await db.commit()
    for doc in uploaded:
        await db.refresh(doc)

    return {
        "message":            f"{len(uploaded)} document(s) uploaded successfully",
        "documents_uploaded": len(uploaded),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. GET documents for a budget
# GET /budget/{budget_id}/documents
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{budget_id}/documents", response_model=list[BudgetDocumentResponse])
async def get_budget_documents(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BudgetDocument).where(
            BudgetDocument.budget_id == budget_id
        )
    )
    return result.scalars().all()


# ─────────────────────────────────────────────────────────────────────────────
# 5. DELETE a document
# DELETE /budget/documents/{doc_id}
# ─────────────────────────────────────────────────────────────────────────────
@router.delete("/documents/{doc_id}")
async def delete_budget_document(
    doc_id: int,
    db:     AsyncSession = Depends(get_db),
):
    doc = await db.get(BudgetDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    budget = await db.get(BudgetProposal, doc.budget_id)
    if budget.status not in ("draft", "revision_requested"):
        raise HTTPException(400, "Cannot delete document after submission")

    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# 6. SUBMIT budget to committee
# POST /budget/{budget_id}/submit
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{budget_id}/submit", response_model=BudgetProposalResponse)
async def submit_budget(
    budget_id: int,
    payload:   BudgetSubmit,
    db:        AsyncSession = Depends(get_db),
):
    budget = await db.get(BudgetProposal, budget_id)
    if not budget:
        raise HTTPException(404, "Budget not found")

    if budget.status not in ("draft", "revision_requested"):
        raise HTTPException(400, f"Cannot submit budget with status '{budget.status}'")

    project = await db.get(Project, budget.project_id)
    if project.project_manager_id != payload.submitted_by:
        raise HTTPException(403, "Only the project manager can submit the budget")

    budget.status       = "submitted"
    budget.submitted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(budget)
    return budget


# ─────────────────────────────────────────────────────────────────────────────
# 7. COMMITTEE REVIEW — approve or request revision
# POST /budget/{budget_id}/review
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{budget_id}/review", response_model=BudgetProposalResponse)
async def review_budget(
    budget_id: int,
    payload:   BudgetReview,
    db:        AsyncSession = Depends(get_db),
):
    budget = await db.get(BudgetProposal, budget_id)
    if not budget:
        raise HTTPException(404, "Budget not found")

    if budget.status != "submitted":
        raise HTTPException(400, "Budget must be submitted before review")

    if payload.action not in ("approved", "revision_requested"):
        raise HTTPException(400, "action must be 'approved' or 'revision_requested'")

    budget.status            = payload.action
    budget.committee_remarks = payload.committee_remarks

    if payload.action == "revision_requested":
        budget.revision_count = (budget.revision_count or 0) + 1

    await db.commit()
    await db.refresh(budget)
    return budget


# ─────────────────────────────────────────────────────────────────────────────
# 8. UPDATE budget (PM edits after revision)
# PUT /budget/{budget_id}
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/{budget_id}", response_model=BudgetProposalResponse)
async def update_budget(
    budget_id: int,
    payload:   BudgetProposalCreate,
    db:        AsyncSession = Depends(get_db),
):
    budget = await db.get(BudgetProposal, budget_id)
    if not budget:
        raise HTTPException(404, "Budget not found")

    if budget.status not in ("draft", "revision_requested"):
        raise HTTPException(
            400, "Budget can only be edited in draft or revision_requested state"
        )

    for key, val in payload.model_dump(
        exclude={"project_id", "created_by"}
    ).items():
        setattr(budget, key, val)

    await db.commit()
    await db.refresh(budget)
    return budget