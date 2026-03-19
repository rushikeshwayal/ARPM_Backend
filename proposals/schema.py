from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProposalCreate(BaseModel):

    title: str
    lead_researcher_id: int
    assigned_pm_id: Optional[int]
    research_domain: Optional[str]


    abstract: Optional[str]
    problem_statement: Optional[str]
    motivation: Optional[str]
    objectives: Optional[str]
    methodology_overview: Optional[str]
    novelty: Optional[str]
    expected_outcomes: Optional[str]
    potential_impact: Optional[str]

    proposed_duration_months: Optional[int]
    rough_budget_estimate: Optional[int]
    team_size_estimate: Optional[int]
    required_resources_summary: Optional[str]


class ProposalResponse(BaseModel):

    id: int
    title: str
    lead_researcher_id: int
    research_domain: Optional[str]
    assigned_pm_id: Optional[int] 

    abstract: Optional[str]
    problem_statement: Optional[str]
    motivation: Optional[str]
    objectives: Optional[str]
    methodology_overview: Optional[str]
    novelty: Optional[str]
    expected_outcomes: Optional[str]
    potential_impact: Optional[str]

    proposed_duration_months: Optional[int]
    rough_budget_estimate: Optional[int]
    team_size_estimate: Optional[int]
    required_resources_summary: Optional[str]

    status: str

    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProposalDocumentResponse(BaseModel):

    id: int
    proposal_id: int
    document_name: str
    document_type: str
    file_path: str
    uploaded_by: int
    uploaded_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProposalUpdate(BaseModel):

    title: Optional[str] = None
    research_domain: Optional[str] = None

    abstract: Optional[str] = None
    problem_statement: Optional[str] = None
    motivation: Optional[str] = None
    objectives: Optional[str] = None
    methodology_overview: Optional[str] = None
    novelty: Optional[str] = None
    expected_outcomes: Optional[str] = None
    potential_impact: Optional[str] = None

    proposed_duration_months: Optional[int] = None
    rough_budget_estimate: Optional[int] = None
    team_size_estimate: Optional[int] = None
    required_resources_summary: Optional[str] = None



class SubmitToPMRequest(BaseModel):
    pm_id: int