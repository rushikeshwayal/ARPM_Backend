from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database import get_db
from PraposalReviewer.models import ProposalReviewer
from PraposalReviewer.schema import (
    ProposalReviewerCreate,
    ProposalReviewerResponse
)

router = APIRouter(
    prefix="/proposal-reviewers",
    tags=["Proposal Reviewers"]
)

@router.post(
    "/",
    response_model=ProposalReviewerResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_reviewer(
    data: ProposalReviewerCreate,
    db: AsyncSession = Depends(get_db)
):
    # 🔥 Prevent duplicate assignment
    existing = await db.execute(
        select(ProposalReviewer).where(
            and_(
                ProposalReviewer.proposal_id == data.proposal_id,
                ProposalReviewer.reviewer_id == data.reviewer_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Reviewer already assigned to this proposal"
        )

    new_reviewer = ProposalReviewer(**data.dict())

    db.add(new_reviewer)
    await db.commit()
    await db.refresh(new_reviewer)

    return new_reviewer

@router.get(
    "/",
    response_model=list[ProposalReviewerResponse]
)
async def get_all_reviewers(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ProposalReviewer))
    reviewers = result.scalars().all()

    return reviewers

@router.get(
    "/{id}",
    response_model=ProposalReviewerResponse
)
async def get_reviewer_by_id(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ProposalReviewer).where(ProposalReviewer.id == id)
    )
    reviewer = result.scalar_one_or_none()

    if not reviewer:
        raise HTTPException(
            status_code=404,
            detail="Reviewer assignment not found"
        )

    return reviewer


@router.get(
    "/proposal/{proposal_id}",
    response_model=list[ProposalReviewerResponse]
)
async def get_reviewers_by_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ProposalReviewer).where(
            ProposalReviewer.proposal_id == proposal_id
        )
    )
    reviewers = result.scalars().all()

    return reviewers

@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK
)
async def delete_reviewer(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ProposalReviewer).where(ProposalReviewer.id == id)
    )
    reviewer = result.scalar_one_or_none()

    if not reviewer:
        raise HTTPException(
            status_code=404,
            detail="Reviewer assignment not found"
        )

    await db.delete(reviewer)
    await db.commit()

    return {"message": "Reviewer assignment deleted successfully"}

@router.patch(
    "/{id}/status",
    response_model=ProposalReviewerResponse
)
async def update_reviewer_status(
    id: int,
    status_value: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ProposalReviewer).where(ProposalReviewer.id == id)
    )
    reviewer = result.scalar_one_or_none()

    if not reviewer:
        raise HTTPException(
            status_code=404,
            detail="Reviewer assignment not found"
        )

    reviewer.status = status_value

    await db.commit()
    await db.refresh(reviewer)

    return reviewer