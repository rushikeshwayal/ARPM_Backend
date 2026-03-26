from fastapi import FastAPI
from users.api import router as user_router
from database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from proposals.api import router as proposal_router
from PraposalReviewer.api import router as proposal_reviewer_router
from ProposalReview.api import router as proposal_review_router
from BudgetProposal.api import router as budget_proposal_router
from Project.api import router as project_router
from Budget_Document.api import router as budget_document_router
from BudgetReleasePlan.api import router as budget_release_plan_router
from ProjectPhase.api import router as project_phase_router
from communication.api import router as message_router
from Dashboard.api import router as dashboard_router



app = FastAPI()


@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(proposal_router)
app.include_router(proposal_reviewer_router)
app.include_router(proposal_review_router)
app.include_router(budget_proposal_router)
app.include_router(budget_document_router)
app.include_router(project_router)
app.include_router(budget_release_plan_router)
app.include_router(project_phase_router)
app.include_router(message_router)
app.include_router(dashboard_router)
