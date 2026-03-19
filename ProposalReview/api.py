from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException,APIRouter

from database import get_db
from proposals.models import Proposal
from ProposalReview.model import ProposalReview
from ProposalReview.schema import ProposalReviewCreate, ProposalReviewResponse

router = APIRouter(prefix="/proposal-reviews", tags=["Proposal Reviews"])
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException, APIRouter

from database import get_db
from proposals.models import Proposal
from ProposalReview.model import ProposalReview
from ProposalReview.schema import ProposalReviewCreate, ProposalReviewResponse

router = APIRouter(prefix="/proposal-reviews", tags=["Proposal Reviews"])


@router.post("/", response_model=ProposalReviewResponse)
async def create_review(
    payload: ProposalReviewCreate,
    db: AsyncSession = Depends(get_db)
):
    # ==============================
    # ✅ CHECK PROPOSAL EXISTS
    # ==============================
    proposal = await db.get(Proposal, payload.proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # ==============================
    # ✅ PREVENT DUPLICATE REVIEW
    # ==============================
    if payload.role == "reviewer":
        existing = await db.execute(
            select(ProposalReview).where(
                ProposalReview.proposal_id == payload.proposal_id,
                ProposalReview.reviewer_id == payload.reviewer_id,
                ProposalReview.role == "reviewer"
            )
        )

        if existing.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="You have already reviewed this proposal"
            )

    # ==============================
    # ✅ CREATE REVIEW
    # ==============================
    review = ProposalReview(
        proposal_id=payload.proposal_id,
        reviewer_id=payload.reviewer_id,
        role=payload.role,
        structured_feedback=payload.structured_feedback,
        general_remark=payload.general_remark,
        decision=payload.decision
    )

    db.add(review)

    # ==============================
    # 🔥 STATUS AUTOMATION
    # ==============================

    # ------------------------------
    # 🧑‍💼 PROJECT MANAGER
    # ------------------------------
    if payload.role == "project_manager":

        if payload.decision == "revise":
            proposal.status = "returned_to_draft"

        elif payload.decision == "approved":   # ✅ FIXED
            proposal.status = "submitted_to_reviewers"

    # ------------------------------
    # 👨‍🔬 REVIEWER
    # ------------------------------
    elif payload.role == "reviewer":

        result = await db.execute(
            select(ProposalReview.reviewer_id).where(
                ProposalReview.proposal_id == payload.proposal_id,
                ProposalReview.role == "reviewer"
            )
        )

        existing_reviewers = set(result.scalars().all())

        # ✅ INCLUDE CURRENT REVIEWER
        existing_reviewers.add(payload.reviewer_id)

        REQUIRED_REVIEWERS = 3  # ⚠️ replace later with dynamic count

        if len(existing_reviewers) >= REQUIRED_REVIEWERS:
            proposal.status = "submitted_to_committee"

    # ------------------------------
    # 🏛️ COMMITTEE
    # ------------------------------
    elif payload.role == "committee":

        if payload.decision == "approve":
            proposal.status = "approved"

        elif payload.decision == "reject":
            proposal.status = "rejected"

    # ==============================
    # ✅ SAVE
    # ==============================
    await db.commit()
    await db.refresh(review)

    return review


# =========================================
# 📥 GET REVIEWS BY PROPOSAL
# =========================================
@router.get("/{proposal_id}", response_model=list[ProposalReviewResponse])
async def get_reviews_by_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(ProposalReview)
        .where(ProposalReview.proposal_id == proposal_id)
        .order_by(ProposalReview.created_at.desc())
    )

    reviews = result.scalars().all()

    return reviews

@router.get("/{proposal_id}", response_model=list[ProposalReviewResponse])
async def get_reviews_by_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(ProposalReview).where(
            ProposalReview.proposal_id == proposal_id
        ).order_by(ProposalReview.created_at.desc())
    )

    reviews = result.scalars().all()

    return reviews