from pydantic import BaseModel
from typing import List


class ProposalStats(BaseModel):
    total: int
    accepted: int
    rejected: int
    pending: int


class BudgetStats(BaseModel):
    sanctioned: float
    released: float


class ProjectStats(BaseModel):
    total: int
    active: int
    completed: int
    on_hold: int


class RecentMessage(BaseModel):
    id: int
    subject: str
    sender_name: str
    sender_email: str
    time: str
    unread: bool

    class Config:
        orm_mode = True


class RecentProject(BaseModel):
    id: int
    name: str
    phase: str
    lead: str
    status: str
    progress: int

    class Config:
        orm_mode = True


class PMDashboardResponse(BaseModel):
    proposals: ProposalStats
    budget: BudgetStats
    projects: ProjectStats
    recent_messages: List[RecentMessage]
    recent_projects: List[RecentProject]

    class Config:
        orm_mode = True