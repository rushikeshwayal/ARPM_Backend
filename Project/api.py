from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from Project.models import Project
from Project.schema import ProjectCreate, ProjectResponse
from proposals.models import Proposal, ProposalStatus

router = APIRouter(prefix="/projects", tags=["Projects"])

# ──────────────────────────────────────────────────────────────────────────────
# ⚠️ ROUTE ORDER: specific string routes MUST come before /{project_id}
# ──────────────────────────────────────────────────────────────────────────────


# 1️⃣ GET /projects/eligible-proposals/{pm_id}
@router.get("/eligible-proposals/{pm_id}")
async def get_eligible_proposals(
    pm_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Proposal).where(
            Proposal.assigned_pm_id == pm_id,
            Proposal.status == ProposalStatus.approved,
        )
    )
    proposals = result.scalars().all()

    used_result = await db.execute(select(Project.proposal_id))
    used_ids = {row[0] for row in used_result.all()}

    return [p for p in proposals if p.id not in used_ids]


# 2️⃣ GET /projects/pm/{pm_id}
@router.get("/pm/{pm_id}", response_model=list[ProjectResponse])
async def get_projects_by_pm(
    pm_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.project_manager_id == pm_id)
    )
    return result.scalars().all()


# 3️⃣ GET /projects/all
@router.get("/all", response_model=list[ProjectResponse])
async def get_all_projects(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project))
    return result.scalars().all()


# ─────────────────────────────────────────────────────────────────────────────
# 4️⃣ GET /projects/researcher/{researcher_id}
#
# Logic:
#   Step 1 — Find all proposals where lead_researcher_id = researcher_id
#             AND status = approved  (only approved proposals become projects)
#   Step 2 — Find all projects whose proposal_id is in that set
#   Step 3 — Return those projects
#
# Why approved only?
#   A project only exists for an approved proposal (enforced at creation).
#   So we only need to look at approved proposals to find the researcher's projects.
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/researcher/{researcher_id}", response_model=list[ProjectResponse])
async def get_projects_by_researcher(
    researcher_id: int,
    db: AsyncSession = Depends(get_db),
):
    # Step 1 — get all approved proposals created by this researcher
    proposal_result = await db.execute(
        select(Proposal.id).where(
            Proposal.lead_researcher_id == researcher_id,
            Proposal.status == ProposalStatus.approved,
        )
    )
    proposal_ids = [row[0] for row in proposal_result.all()]

    if not proposal_ids:
        return []

    # Step 2 — get all projects linked to those proposals
    project_result = await db.execute(
        select(Project).where(
            Project.proposal_id.in_(proposal_ids)
        )
    )
    return project_result.scalars().all()


# 5️⃣ POST /projects/
@router.post("/", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    proposal = await db.get(Proposal, payload.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != ProposalStatus.approved:
        raise HTTPException(status_code=400, detail="Proposal is not approved")

    if proposal.assigned_pm_id != payload.project_manager_id:
        raise HTTPException(status_code=403, detail="Not authorized for this proposal")

    existing = await db.execute(
        select(Project).where(Project.proposal_id == payload.proposal_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A project already exists for this proposal")

    project = Project(**payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


# 6️⃣ GET /projects/{project_id}  ← MUST be last
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project