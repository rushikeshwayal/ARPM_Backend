from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import datetime, timezone

from database import get_db
from BudgetReleasePlan.model import BudgetReleasePlan, BudgetTranche
from BudgetReleasePlan.schema import (
    ReleasePlanCreate, ReleasePlanResponse,
    TrancheCreate, TrancheUpdate, TrancheRelease, TrancheResponse,
)
from BudgetProposal.models import BudgetProposal
from services.google_drive import upload_file_to_drive

router = APIRouter(prefix="/release-plan", tags=["Budget Release Plan"])


# ── Helper ────────────────────────────────────────────────────────────────────
# ✅ Always use selectinload when fetching plans — never rely on lazy load in async

async def _get_plan_with_tranches(project_id: int, db: AsyncSession):
    """Fetch latest plan for a project WITH tranches eagerly loaded."""
    result = await db.execute(
        select(BudgetReleasePlan)
        .where(BudgetReleasePlan.project_id == project_id)
        .options(selectinload(BudgetReleasePlan.tranches))   # ✅ eager load
        .order_by(BudgetReleasePlan.plan_version.desc())
    )
    return result.scalar_one_or_none()


async def _get_plan_by_id_with_tranches(plan_id: int, db: AsyncSession):
    """Fetch plan by ID WITH tranches eagerly loaded."""
    result = await db.execute(
        select(BudgetReleasePlan)
        .where(BudgetReleasePlan.id == plan_id)
        .options(selectinload(BudgetReleasePlan.tranches))   # ✅ eager load
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Release plan not found")
    return plan


def _build_response(plan: BudgetReleasePlan) -> ReleasePlanResponse:
    """Build response with computed summary fields."""
    tranches = plan.tranches or []   # ✅ guard against None
    allocated = sum(t.amount         for t in tranches)
    released  = sum(t.released_amount or Decimal(0) for t in tranches)
    remaining = plan.total_sanctioned_amount - released

    resp = ReleasePlanResponse.model_validate(plan)
    resp.total_allocated = allocated
    resp.total_released  = released
    resp.remaining       = remaining
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE ORDER: specific string paths MUST come before /{plan_id}
# ─────────────────────────────────────────────────────────────────────────────


# 1. GET /release-plan/project/{project_id}
@router.get("/project/{project_id}", response_model=ReleasePlanResponse)
async def get_plan(project_id: int, db: AsyncSession = Depends(get_db)):
    plan = await _get_plan_with_tranches(project_id, db)
    if not plan:
        raise HTTPException(404, "No release plan found")
    return _build_response(plan)


# 2. POST /release-plan/  — Create plan
@router.post("/", response_model=ReleasePlanResponse)
async def create_plan(payload: ReleasePlanCreate, db: AsyncSession = Depends(get_db)):

    budget_result = await db.execute(
        select(BudgetProposal).where(BudgetProposal.project_id == payload.project_id)
    )
    budget = budget_result.scalar_one_or_none()
    if not budget or budget.status != "approved":
        raise HTTPException(400, "Budget must be approved before creating a release plan")

    existing_result = await db.execute(
        select(BudgetReleasePlan).where(
            BudgetReleasePlan.project_id == payload.project_id,
            BudgetReleasePlan.status.in_(["draft", "active", "locked"])
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(400, "An active or draft release plan already exists")

    plan = BudgetReleasePlan(**payload.model_dump())
    db.add(plan)
    await db.commit()

    # ✅ Re-fetch with selectinload so tranches list is [] not None
    plan = await _get_plan_with_tranches(payload.project_id, db)
    return _build_response(plan)


# 3. POST /release-plan/tranches/{tranche_id}/upload
@router.post("/tranches/{tranche_id}/upload")
async def upload_tranche_doc(
    tranche_id:  int,
    uploaded_by: int         = Form(...),
    doc_type:    str         = Form(...),
    file:        UploadFile  = File(...),
    db:          AsyncSession = Depends(get_db),
):
    tranche = await db.get(BudgetTranche, tranche_id)
    if not tranche:
        raise HTTPException(404, "Tranche not found")

    file_bytes = await file.read()
    drive_url  = upload_file_to_drive(file_bytes, file.filename)

    if doc_type == "justification":
        tranche.tranche_justification_doc_url = drive_url
    elif doc_type == "approval":
        tranche.release_approval_doc_url = drive_url
    else:
        raise HTTPException(400, "doc_type must be 'justification' or 'approval'")

    await db.commit()
    return {"message": f"{doc_type} document uploaded", "url": drive_url}


# 4. POST /release-plan/tranches/{tranche_id}/release
@router.post("/tranches/{tranche_id}/release", response_model=TrancheResponse)
async def release_tranche(
    tranche_id: int,
    payload:    TrancheRelease,
    db:         AsyncSession = Depends(get_db),
):
    tranche = await db.get(BudgetTranche, tranche_id)
    if not tranche:
        raise HTTPException(404, "Tranche not found")

    plan = await db.get(BudgetReleasePlan, tranche.plan_id)
    if plan.status != "active":
        raise HTTPException(400, "Plan must be active to release tranches")
    if tranche.status == "released":
        raise HTTPException(400, "Tranche already released")
    if payload.released_amount > tranche.amount:
        raise HTTPException(400, "Released amount cannot exceed tranche amount")

    tranche.status                = "released"
    tranche.released_amount       = payload.released_amount
    tranche.release_date          = datetime.now(timezone.utc)
    tranche.released_by           = payload.released_by
    tranche.transaction_reference = payload.transaction_reference
    tranche.remarks               = payload.remarks

    await db.commit()
    await db.refresh(tranche)
    return tranche


# 5. PUT /release-plan/tranches/{tranche_id}
@router.put("/tranches/{tranche_id}", response_model=TrancheResponse)
async def update_tranche(
    tranche_id: int,
    payload:    TrancheUpdate,
    db:         AsyncSession = Depends(get_db),
):
    tranche = await db.get(BudgetTranche, tranche_id)
    if not tranche:
        raise HTTPException(404, "Tranche not found")

    plan = await db.get(BudgetReleasePlan, tranche.plan_id)
    if plan.status != "draft":
        raise HTTPException(400, "Tranches can only be edited on a draft plan")

    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(tranche, key, val)

    await db.commit()
    await db.refresh(tranche)
    return tranche


# 6. DELETE /release-plan/tranches/{tranche_id}
@router.delete("/tranches/{tranche_id}")
async def delete_tranche(tranche_id: int, db: AsyncSession = Depends(get_db)):
    tranche = await db.get(BudgetTranche, tranche_id)
    if not tranche:
        raise HTTPException(404, "Tranche not found")

    plan = await db.get(BudgetReleasePlan, tranche.plan_id)
    if plan.status != "draft":
        raise HTTPException(400, "Tranches can only be deleted from a draft plan")
    if tranche.status == "released":
        raise HTTPException(400, "Cannot delete a released tranche")

    await db.delete(tranche)
    await db.commit()
    return {"message": "Tranche deleted"}


# 7. POST /release-plan/{plan_id}/activate
@router.post("/{plan_id}/activate", response_model=ReleasePlanResponse)
async def activate_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan = await _get_plan_by_id_with_tranches(plan_id, db)

    if plan.status != "draft":
        raise HTTPException(400, f"Only draft plans can be activated (current: {plan.status})")

    tranches = plan.tranches or []
    if not tranches:
        raise HTTPException(400, "Plan must have at least one tranche before activation")

    total_tranche = sum(t.amount for t in tranches)
    if total_tranche > plan.total_sanctioned_amount:
        raise HTTPException(
            400,
            f"Total tranche amount (₹{total_tranche}) exceeds sanctioned budget (₹{plan.total_sanctioned_amount})"
        )

    has_initial = any(t.condition_type in ("manual", "phase_start") for t in tranches)
    if not has_initial:
        raise HTTPException(
            400,
            "Plan must contain at least one Manual or Phase Start tranche as initial funding"
        )

    plan.status = "active"
    await db.commit()

    plan = await _get_plan_by_id_with_tranches(plan_id, db)
    return _build_response(plan)


# 8. POST /release-plan/{plan_id}/revise
@router.post("/{plan_id}/revise", response_model=ReleasePlanResponse)
async def revise_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    old = await _get_plan_by_id_with_tranches(plan_id, db)

    if old.status not in ("active", "locked"):
        raise HTTPException(400, "Only active or locked plans can be revised")

    old.status = "archived"
    new_plan = BudgetReleasePlan(
        project_id              = old.project_id,
        total_sanctioned_amount = old.total_sanctioned_amount,
        currency                = old.currency,
        plan_version            = old.plan_version + 1,
        created_by              = old.created_by,
        status                  = "draft",
        notes                   = f"Revised from v{old.plan_version}",
    )
    db.add(new_plan)
    await db.commit()

    new_plan = await _get_plan_with_tranches(new_plan.project_id, db)
    return _build_response(new_plan)


# 9. POST /release-plan/{plan_id}/tranches  ← LAST, after all /tranches/... routes
@router.post("/{plan_id}/tranches", response_model=TrancheResponse)
async def add_tranche(
    plan_id: int,
    payload: TrancheCreate,
    db:      AsyncSession = Depends(get_db),
):
    plan = await _get_plan_by_id_with_tranches(plan_id, db)

    if plan.status != "draft":
        raise HTTPException(400, "Tranches can only be added to a draft plan")

    tranches  = plan.tranches or []
    allocated = sum(t.amount for t in tranches)
    if allocated + payload.amount > plan.total_sanctioned_amount:
        raise HTTPException(
            400,
            f"Adding ₹{payload.amount} would exceed sanctioned budget of ₹{plan.total_sanctioned_amount}"
        )

    tranche = BudgetTranche(plan_id=plan_id, **payload.model_dump())
    db.add(tranche)
    await db.commit()
    await db.refresh(tranche)
    return tranche