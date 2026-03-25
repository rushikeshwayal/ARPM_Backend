from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from ProjectPhase.models import ProjectPhase, PhaseStep, PhaseStepDocument
from ProjectPhase.schema import (
    PhaseActivate, PhaseSubmit, PhaseReview,
    PhaseResponse, PhaseVisibilityResponse,
    StepContentUpdate, StepResponse,
)
from ProjectPhase.constants import PREDEFINED_PHASES, PHASE_STEPS, STEP_DOCUMENT_TYPES
from BudgetReleasePlan.model import BudgetReleasePlan
from Project.models import Project
from services.google_drive import upload_file_to_drive

router = APIRouter(prefix="/phases", tags=["Phases"])


# ── Inline schemas for JSON body endpoints ────────────────────────────────────
class StepSubmitBody(BaseModel):
    submitted_by: int

class StepReviewBody(BaseModel):
    reviewed_by: int

class StepReturnBody(BaseModel):
    returned_by: int
    remarks:     Optional[str] = None

class PhaseSubmitBody(BaseModel):
    submitted_by: int

class CustomStepCreate(BaseModel):
    step_number: int
    step_name:   str
    description: Optional[str] = None

class CustomPhaseCreate(BaseModel):
    phase_name:   str
    description:  Optional[str] = None
    phase_number: int
    iteration:    int  = 1
    is_custom:    bool = True
    created_by:   int
    steps:        List[CustomStepCreate] = []


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_phase(phase_id: int, db: AsyncSession) -> ProjectPhase:
    result = await db.execute(
        select(ProjectPhase)
        .where(ProjectPhase.id == phase_id)
        .options(selectinload(ProjectPhase.steps).selectinload(PhaseStep.documents))
    )
    phase = result.scalar_one_or_none()
    if not phase:
        raise HTTPException(404, "Phase not found")
    return phase


async def _load_phases(project_id: int, db: AsyncSession) -> List[ProjectPhase]:
    result = await db.execute(
        select(ProjectPhase)
        .where(ProjectPhase.project_id == project_id)
        .options(selectinload(ProjectPhase.steps).selectinload(PhaseStep.documents))
        .order_by(ProjectPhase.phase_number)
    )
    return result.scalars().all()


async def _count_released_tranches(project_id: int, db: AsyncSession) -> int:
    plan_result = await db.execute(
        select(BudgetReleasePlan)
        .where(
            BudgetReleasePlan.project_id == project_id,
            BudgetReleasePlan.status.in_(["active", "locked"])
        )
        .options(selectinload(BudgetReleasePlan.tranches))
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        return 0
    return sum(1 for t in (plan.tranches or []) if t.status == "released")


def _build_phase_response(phase: ProjectPhase) -> PhaseResponse:
    steps     = phase.steps or []
    completed = sum(1 for s in steps if s.status == "reviewed")
    total     = len(steps)
    resp = PhaseResponse.model_validate(phase)
    resp.total_steps     = total
    resp.completed_steps = completed
    resp.progress_pct    = round((completed / total) * 100) if total > 0 else 0
    return resp


async def _seed_phases_for_project(project_id: int, db: AsyncSession):
    for phase_def in PREDEFINED_PHASES:
        phase = ProjectPhase(
            project_id   = project_id,
            phase_number = phase_def["phase_number"],
            phase_name   = phase_def["phase_name"],
            description  = phase_def["description"],
            status       = "not_started",
        )
        db.add(phase)
        await db.flush()
        for step_def in PHASE_STEPS.get(phase_def["phase_number"], []):
            db.add(PhaseStep(
                phase_id    = phase.id,
                step_number = step_def["step_number"],
                step_name   = step_def["step_name"],
                description = step_def["description"],
                status      = "not_started",
            ))
    await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  ROUTE ORDER — all /steps/... and /project/... MUST come before /{phase_id}
# ─────────────────────────────────────────────────────────────────────────────


# 1. GET /phases/project/{project_id}
@router.get("/project/{project_id}", response_model=PhaseVisibilityResponse)
async def get_phases(project_id: int, db: AsyncSession = Depends(get_db)):
    released_count = await _count_released_tranches(project_id, db)
    if released_count == 0:
        return PhaseVisibilityResponse(
            visible=False,
            reason="No budget tranche released yet.",
            tranche_released_count=0,
            phases=[],
        )
    existing = await _load_phases(project_id, db)
    if not existing:
        await _seed_phases_for_project(project_id, db)
        existing = await _load_phases(project_id, db)
    return PhaseVisibilityResponse(
        visible=True,
        reason=f"{released_count} tranche(s) released.",
        tranche_released_count=released_count,
        phases=[_build_phase_response(p) for p in existing],
    )


# 2. POST /phases/project/{project_id}/custom
@router.post("/project/{project_id}/custom", response_model=PhaseResponse)
async def create_custom_phase(
    project_id: int,
    payload:    CustomPhaseCreate,
    db:         AsyncSession = Depends(get_db),
):
    released = await _count_released_tranches(project_id, db)
    if released == 0:
        raise HTTPException(400, "Cannot add phases — no budget tranche released")
    phase = ProjectPhase(
        project_id   = project_id,
        phase_number = payload.phase_number,
        phase_name   = payload.phase_name,
        description  = payload.description,
        status       = "not_started",
        iteration    = payload.iteration,
        is_custom    = payload.is_custom,
    )
    db.add(phase)
    await db.flush()
    for step_def in payload.steps:
        db.add(PhaseStep(
            phase_id    = phase.id,
            step_number = step_def.step_number,
            step_name   = step_def.step_name,
            description = step_def.description,
            status      = "not_started",
        ))
    await db.commit()
    phase = await _load_phase(phase.id, db)
    return _build_phase_response(phase)


# 3. GET /phases/steps/{step_id}/document-types
@router.get("/steps/{step_id}/document-types")
async def get_step_document_types(step_id: int, db: AsyncSession = Depends(get_db)):
    step = await db.get(PhaseStep, step_id)
    if not step:
        raise HTTPException(404, "Step not found")
    phase    = await db.get(ProjectPhase, step.phase_id)
    doc_types = STEP_DOCUMENT_TYPES.get(phase.phase_number, {}).get(step.step_number, [])
    return {"step_id": step_id, "document_types": doc_types}


# 4. POST /phases/steps/{step_id}/upload
@router.post("/steps/{step_id}/upload")
async def upload_step_document(
    step_id:        int,
    uploaded_by:    int         = Form(...),
    document_title: str         = Form(...),
    document_type:  str         = Form(...),
    file:           UploadFile  = File(...),
    db:             AsyncSession = Depends(get_db),
):
    step = await db.get(PhaseStep, step_id)
    if not step:
        raise HTTPException(404, "Step not found")
    if step.status == "reviewed":
        raise HTTPException(400, "Cannot upload to a reviewed step")

    file_bytes = await file.read()
    drive_url  = upload_file_to_drive(file_bytes, file.filename)
    db.add(PhaseStepDocument(
        step_id        = step_id,
        document_title = document_title,
        document_type  = document_type,
        file_path      = drive_url,
        uploaded_by    = uploaded_by,
    ))
    if step.status == "not_started":
        step.status     = "in_progress"
        step.started_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Document uploaded", "url": drive_url}


# 5. DELETE /phases/steps/documents/{doc_id}
#    ⚠️ Must be BEFORE /steps/{step_id}/... routes — "documents" must not match as step_id
@router.delete("/steps/documents/{doc_id}")
async def delete_step_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(PhaseStepDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    step = await db.get(PhaseStep, doc.step_id)
    if step.status in ("submitted", "reviewed"):
        raise HTTPException(400, "Cannot delete document from submitted/reviewed step")
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


# 6. PUT /phases/steps/{step_id}/content
@router.put("/steps/{step_id}/content", response_model=StepResponse)
async def update_step_content(
    step_id: int,
    payload: StepContentUpdate,
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PhaseStep).where(PhaseStep.id == step_id)
        .options(selectinload(PhaseStep.documents))
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")
    if step.status in ("submitted", "reviewed"):
        raise HTTPException(400, "Cannot edit a submitted or reviewed step")
    phase = await db.get(ProjectPhase, step.phase_id)
    if phase.status not in ("active", "revision_requested"):
        raise HTTPException(400, "Phase must be active to edit steps")
    if step.step_number > 1:
        prev = (await db.execute(
            select(PhaseStep).where(
                PhaseStep.phase_id    == step.phase_id,
                PhaseStep.step_number == step.step_number - 1
            )
        )).scalar_one_or_none()
        if prev and prev.status != "reviewed":
            raise HTTPException(400, f"Step {step.step_number - 1} ({prev.step_name}) must be completed first")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(step, key, val)
    if step.status == "not_started":
        step.status     = "draft"
        step.started_at = datetime.now(timezone.utc)
    elif step.status == "draft":
        step.status = "in_progress"
    await db.commit()
    await db.refresh(step)
    return step


# 7. POST /phases/steps/{step_id}/submit  (JSON body)
@router.post("/steps/{step_id}/submit", response_model=StepResponse)
async def submit_step(
    step_id: int,
    payload: StepSubmitBody,
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PhaseStep).where(PhaseStep.id == step_id)
        .options(selectinload(PhaseStep.documents))
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")
    if step.status == "reviewed":
        raise HTTPException(400, "Step already reviewed")
    if step.status == "not_started":
        raise HTTPException(400, "Add content before submitting")

    phase    = await db.get(ProjectPhase, step.phase_id)
    req_docs = STEP_DOCUMENT_TYPES.get(phase.phase_number, {}).get(step.step_number, [])
    required = [d["type"] for d in req_docs if d.get("required")]
    if required:
        uploaded = {doc.document_type for doc in (step.documents or [])}
        missing  = [r for r in required if r not in uploaded]
        if missing:
            raise HTTPException(400, f"Required documents missing: {', '.join(missing)}")

    step.status       = "submitted"
    step.submitted_by = payload.submitted_by
    step.submitted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(step)
    return step


# 8. POST /phases/steps/{step_id}/review  (JSON body)
@router.post("/steps/{step_id}/review", response_model=StepResponse)
async def review_step(
    step_id: int,
    payload: StepReviewBody,
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PhaseStep).where(PhaseStep.id == step_id)
        .options(selectinload(PhaseStep.documents))
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")
    if step.status != "submitted":
        raise HTTPException(400, "Step must be submitted before review")
    step.status      = "reviewed"
    step.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(step)
    return step


# 9. POST /phases/steps/{step_id}/return  ✅ NEW — PM returns step to researcher
@router.post("/steps/{step_id}/return", response_model=StepResponse)
async def return_step(
    step_id: int,
    payload: StepReturnBody,
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PhaseStep).where(PhaseStep.id == step_id)
        .options(selectinload(PhaseStep.documents))
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")
    if step.status != "submitted":
        raise HTTPException(400, "Only submitted steps can be returned")

    # Reset so researcher can re-edit
    step.status      = "in_progress"
    step.reviewed_at = None

    # Prepend PM remarks to notes so researcher sees them
    if payload.remarks:
        existing = step.notes or ""
        step.notes = f"[PM: {payload.remarks}]\n\n{existing}".strip()

    await db.commit()
    await db.refresh(step)
    return step


# ── Phase-level routes — /{phase_id} MUST be last ─────────────────────────────

# 10. POST /phases/{phase_id}/activate
@router.post("/{phase_id}/activate", response_model=PhaseResponse)
async def activate_phase(
    phase_id: int,
    payload:  PhaseActivate,
    db:       AsyncSession = Depends(get_db),
):
    phase = await _load_phase(phase_id, db)
    if phase.status != "not_started":
        raise HTTPException(400, f"Phase is already {phase.status}")
    released = await _count_released_tranches(phase.project_id, db)
    if released == 0:
        raise HTTPException(400, "No budget tranche released — cannot activate phase")
    if phase.phase_number > 1:
        prev = (await db.execute(
            select(ProjectPhase).where(
                ProjectPhase.project_id   == phase.project_id,
                ProjectPhase.phase_number == phase.phase_number - 1
            )
        )).scalar_one_or_none()
        if not prev or prev.status != "completed":
            raise HTTPException(400, f"Phase {phase.phase_number - 1} must be completed first")
    phase.status       = "active"
    phase.activated_by = payload.activated_by
    phase.activated_at = datetime.now(timezone.utc)
    await db.commit()
    return _build_phase_response(await _load_phase(phase_id, db))


# 11. POST /phases/{phase_id}/submit  (JSON body)
@router.post("/{phase_id}/submit", response_model=PhaseResponse)
async def submit_phase(
    phase_id: int,
    payload:  PhaseSubmitBody,
    db:       AsyncSession = Depends(get_db),
):
    phase = await _load_phase(phase_id, db)
    if phase.status not in ("active", "revision_requested"):
        raise HTTPException(400, f"Phase must be active or in revision (current: {phase.status})")
    steps = phase.steps or []
    if not steps:
        raise HTTPException(400, "Phase has no steps")
    unreviewed = [s for s in steps if s.status != "reviewed"]
    if unreviewed:
        raise HTTPException(400, f"Complete all steps first: {', '.join(s.step_name for s in unreviewed)}")
    phase.status       = "submitted"
    phase.submitted_by = payload.submitted_by
    phase.submitted_at = datetime.now(timezone.utc)
    await db.commit()
    return _build_phase_response(await _load_phase(phase_id, db))


# 12. POST /phases/{phase_id}/review
@router.post("/{phase_id}/review", response_model=PhaseResponse)
async def review_phase(
    phase_id: int,
    payload:  PhaseReview,
    db:       AsyncSession = Depends(get_db),
):
    phase = await _load_phase(phase_id, db)
    if phase.status != "submitted":
        raise HTTPException(400, "Phase must be submitted before review")
    if payload.action not in ("approved", "revision_requested"):
        raise HTTPException(400, "action must be 'approved' or 'revision_requested'")
    phase.reviewed_by = payload.reviewed_by
    phase.pm_remarks  = payload.pm_remarks
    if payload.action == "approved":
        phase.status       = "completed"
        phase.completed_at = datetime.now(timezone.utc)
    else:
        phase.status         = "revision_requested"
        phase.revision_count = (phase.revision_count or 0) + 1
        for step in (phase.steps or []):
            if step.status == "reviewed":
                step.status = "in_progress"
    await db.commit()
    return _build_phase_response(await _load_phase(phase_id, db))


# 13. GET /phases/{phase_id}  ← MUST be last
@router.get("/{phase_id}", response_model=PhaseResponse)
async def get_phase(phase_id: int, db: AsyncSession = Depends(get_db)):
    return _build_phase_response(await _load_phase(phase_id, db))