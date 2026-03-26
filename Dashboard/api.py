from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from typing import Optional
from datetime import datetime

from database import get_db
from communication.models import Message
from Project.models import Project
from BudgetReleasePlan.model import BudgetReleasePlan, BudgetTranche
from ProjectPhase.models import ProjectPhase
from proposals.models import Proposal, ProposalStatus
from users.models import User
from Dashboard.schema import PMDashboardResponse

router = APIRouter(prefix="/dashboard", tags=["PM Dashboard"])


def _fmt_time(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    delta = datetime.utcnow() - dt.replace(tzinfo=None)
    if delta.days == 0:
        return "Today"
    elif delta.days == 1:
        return "Yesterday"
    return dt.strftime("%d %b")


@router.get("/{pm_id}", response_model=PMDashboardResponse)
async def get_pm_dashboard(pm_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # ── 1. Proposal Stats ─────────────────────────
        result = await db.execute(
            select(
                func.count().label("total"),
                func.sum(case((Proposal.status == ProposalStatus.approved, 1), else_=0)).label("accepted"),
                func.sum(case((Proposal.status == ProposalStatus.rejected, 1), else_=0)).label("rejected"),
                func.sum(case(
                    (Proposal.status.in_([
                        ProposalStatus.submitted_to_pm,
                        ProposalStatus.submitted_to_reviewers,
                        ProposalStatus.review_completed,
                        ProposalStatus.submitted_to_committee,
                    ]), 1),
                    else_=0,
                )).label("pending"),
            ).where(Proposal.assigned_pm_id == pm_id)
        )
        pc = result.one()

        # ── 2. Project Stats ─────────────────────────
        pr = await db.execute(
            select(
                func.count().label("total"),
                func.sum(case((Project.status == "active", 1), else_=0)).label("active"),
                func.sum(case((Project.status == "completed", 1), else_=0)).label("completed"),
                func.sum(case((Project.status == "on_hold", 1), else_=0)).label("on_hold"),
            ).where(Project.project_manager_id == pm_id)
        )
        prc = pr.one()

        proj_ids_q = await db.execute(
            select(Project.id).where(Project.project_manager_id == pm_id)
        )
        project_ids = [r[0] for r in proj_ids_q.all()]

        # ── 3. Budget Stats ─────────────────────────
        if project_ids:
            sanctioned = await db.scalar(
                select(func.coalesce(func.sum(BudgetReleasePlan.total_sanctioned_amount), 0))
                .where(
                    BudgetReleasePlan.project_id.in_(project_ids),
                    BudgetReleasePlan.status.in_(["active", "locked"]),
                )
            )
            released = await db.scalar(
                select(func.coalesce(func.sum(BudgetTranche.released_amount), 0))
                .join(BudgetReleasePlan, BudgetTranche.plan_id == BudgetReleasePlan.id)
                .where(
                    BudgetReleasePlan.project_id.in_(project_ids),
                    BudgetTranche.status == "released",
                )
            )
        else:
            sanctioned, released = 0, 0

        # ── 4. Recent Messages ──────────────────────
        msgs_q = await db.execute(
            select(Message)
            .where(Message.receiver_id == pm_id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        msgs = msgs_q.scalars().all()

        sender_ids = list({m.sender_id for m in msgs})

        sender_map = {}
        if sender_ids:
            senders_q = await db.execute(
                select(User.id, User.email).where(User.id.in_(sender_ids))
            )
            sender_map = {r.id: r for r in senders_q.all()}

        recent_messages = []
        for m in msgs:
            sender = sender_map.get(m.sender_id)

            recent_messages.append({
                "id": m.id,
                "subject": m.subject,
                "sender_name": sender.email if sender else "Unknown",
                "sender_email": sender.email if sender else "",
                "time": _fmt_time(m.created_at),
                "unread": m.created_at.date() == datetime.utcnow().date() if m.created_at else False,
            })

        # ── 5. Recent Projects ──────────────────────
        projs_q = await db.execute(
            select(Project)
            .where(Project.project_manager_id == pm_id)
            .order_by(Project.created_at.desc())
            .limit(4)
        )
        projs = projs_q.scalars().all()

        recent_projects = []
        for proj in projs:

            phase_q = await db.execute(
                select(ProjectPhase)
                .where(ProjectPhase.project_id == proj.id, ProjectPhase.status == "active")
                .limit(1)
            )
            phase = phase_q.scalar_one_or_none()

            if not phase:
                phase_q = await db.execute(
                    select(ProjectPhase)
                    .where(ProjectPhase.project_id == proj.id)
                    .order_by(ProjectPhase.phase_number.desc())
                    .limit(1)
                )
                phase = phase_q.scalar_one_or_none()

            total_phases = await db.scalar(
                select(func.count()).where(ProjectPhase.project_id == proj.id)
            )
            completed_phases = await db.scalar(
                select(func.count()).where(
                    ProjectPhase.project_id == proj.id,
                    ProjectPhase.status == "completed",
                )
            )

            progress = round((completed_phases / total_phases) * 100) if total_phases else 0

            lead_q = await db.execute(
                select(User.email)
                .join(Proposal, Proposal.lead_researcher_id == User.id)
                .where(Proposal.id == proj.proposal_id)
            )
            lead_row = lead_q.first()

            recent_projects.append({
                "id": proj.id,
                "name": proj.title,
                "phase": f"Phase {phase.phase_number}" if phase else "—",
                "lead": lead_row[0] if lead_row else "Unknown",
                "status": proj.status,
                "progress": progress,
            })

        return {
            "proposals": {
                "total": pc.total or 0,
                "accepted": pc.accepted or 0,
                "rejected": pc.rejected or 0,
                "pending": pc.pending or 0,
            },
            "budget": {
                "sanctioned": float(sanctioned or 0),
                "released": float(released or 0),
            },
            "projects": {
                "total": prc.total or 0,
                "active": prc.active or 0,
                "completed": prc.completed or 0,
                "on_hold": prc.on_hold or 0,
            },
            "recent_messages": recent_messages,
            "recent_projects": recent_projects,
        }

    except Exception as e:
        print("❌ ERROR IN DASHBOARD API:", e)
        raise e